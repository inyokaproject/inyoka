"""
    inyoka.wiki.models
    ~~~~~~~~~~~~~~~~~~

    This module implements the database models for the wiki.  It's important
    to know that this doesn't automatically mean that an operation hits the
    database.  In fact most operations will happen either on the caching
    system or the python layer.  Operations that hit the database are all
    native django query methods (which are left untouched) and those that
    are documented to do so.

    This module implements far more models that are acutually in use in the
    `actions`.  This is because the `Page` model and the `PageManager` also
    manage other models such as `Revision`, `Text` and of course also the
    special `Attachment` model which in fact never leaves the module except
    for read only access.

    For details about manipulating and querying objects check out the
    `PageManager` documentation as well as the `Page` documentation.  If you
    just want infos about the models as such that are passed to the template
    context see `Page`, `Attachment`, `Revision`, `Text` and `Diff`.


    Meta Data
    =========

    Meta data keys starting with an capital X, followed by an dash are used
    internally.  Some of them have a special meaning, others are ignored by
    the software until they get a meaning by code updates.

    The following keys are currently in use:

    ``X-Link``
        For every internal link in the page an ``X-Link`` is emitted.  This is
        used by the wiki system to look up backlinks, invalidate caches,
        find missing pages or orphans etc.  Links that leave the parser are
        considered "implicitly relative" which means that they are always
        joined with the current page name.  If a parser wants to avoid that
        it must prefix it with an slash before emitting it.

    ``X-Attach``
        Works like ``X-Link`` but this is emitted if a page is included with
        a macro that displays a page inline.  Examples are the `Picture` or
        the `Include` macro.  This is also considered being an "implicit
        relative" reference thus if something just accepts an absolute link
        this must prefix it with an slash.

    ``X-Redirect``
        Marks this page as redirect to another page.  This should be an
        absolute link to an existing page.

    ``X-Behave``
        Gives the page a behavior.  This is used by the `storage` system and
        documented as part of that module.

    ``X-Cache-Time``
        This is used to give the page a different cache time than the default.

    ``X-Owner``
        Every user or group (prefixed with an ``'@'``) defined this way is
        added to the special ACL ``@Owner`` group.  This is for example used
        for user wiki pages that should only give moderators, administrators
        and the owner of the page access.

    Every internal key is only modifiable by people with the ``PRIV_MANAGE``
    privilege.  Some keys like `X-Link` and `X-Attach` that are defined also
    by the wiki parser itself are marked as `LENIENT_METADATA_KEYS` which
    gives users without the `PRIV_MANAGE` privilege to edit them.

    Apart of those users without this privilege will see the metadata in their
    editor but if they try to send changed metadata back to the database the
    wiki will avoid that.  The models itself do not test for changed metadata
    that is part of the `acl` system.


    :copyright: (c) 2007-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import locale
import random
import time
from collections import defaultdict
from datetime import datetime
from functools import partial
from hashlib import sha1
from typing import Optional

import magic
from django.apps import apps
from django.conf import settings
from django.core.cache import cache
from django.db import models
from django.db.models import Count
from django.db.models.functions import Upper
from django.template.loader import render_to_string
from django.utils.functional import cached_property
from django.utils.html import escape
from django.utils.translation import get_language, gettext_lazy, to_locale
from django.utils.translation import gettext as _
from werkzeug.utils import secure_filename

from inyoka.markup import base as markup
from inyoka.markup import nodes, templates
from inyoka.markup.parsertools import MultiMap
from inyoka.utils.database import InyokaMarkupField
from inyoka.utils.dates import datetime_to_timezone, format_datetime
from inyoka.utils.decorators import deferred
from inyoka.utils.diff3 import generate_udiff, get_close_matches, prepare_udiff
from inyoka.utils.highlight import highlight_code
from inyoka.utils.html import striptags
from inyoka.utils.local import local as local_cache
from inyoka.utils.logger import logger
from inyoka.utils.text import (
    get_pagetitle,
    join_pagename,
    wiki_slugify,
)
from inyoka.utils.urls import href
from inyoka.wiki.exceptions import CaseSensitiveException
from inyoka.wiki.tasks import (
    render_one_revision,
    update_page_by_slug,
    update_related_pages,
)

# maximum number of bytes for metadata.  everything above is truncated
MAX_METADATA = 2 << 8


def is_privileged_wiki_page(name):
    return any(name.startswith(n) for n in settings.WIKI_PRIVILEGED_PAGES)


to_page_by_slug_key = lambda name: f'wiki/page_by_slug/{wiki_slugify(name)}'


class PageManager(models.Manager):
    """
    Because our table definitions are rather complex due to shared text,
    revisions etc the `PageManager` binds some of those attributes
    directly on the page object to give a simpler interface in templates.

    The `PageManager` singleton instance is available as `Page.objects`.
    """

    def exists(self, name, cached=True):
        """
        Returns `True` if `name` exists, the results are cached in a
        request local object to avoid cache or db requests if possible.

        `name` gets slugified with `wiki_slugify()` before.
        """
        if cached:
            if not hasattr(local_cache, 'slug_list'):
                local_cache.slug_list = self.get_slug_list()
            slug_list = local_cache('slug_list')
        else:
            slug_list = self.get_slug_list()
        return wiki_slugify(name) in slug_list

    def get_head(self, name, offset=0):
        """
        Return the revision ID for head or with an offset.  The offset
        can be an negative or positive number, but despite that always
        the absolute number is used.  This is useful if you want the non
        head revision, say to compare head with head - 1 you can call
        ``Page.objects.get_head("Page_Name", -1)``.
        """
        revs = Revision.objects.filter(page__name=name) \
                               .order_by('-id') \
                               .values_list('id', flat=True)
        revs = revs[abs(offset):abs(offset) + 1]
        if revs:
            return revs[0]

    def get_taglist(self, size_limit=None):
        """
        Get a list of all tags or just the most used ones (if size_limit is
        set). Note that this is one of the few operations that also returns
        attachments, not only pages.  The tag list is an ordinary list of
        dicts with the following keys:

        ``'name'``
            The name of the tag

        ``'count'``
            Number of pages flagged with this tag.

        ``'size'``:
            The size of a page as an integer within 1 and 10 in relation to
            the highest count value. One page means a size of 1. The tag with
            the highest count value has the size 10.
        """
        tags = MetaData.objects.filter(key='tag').values_list('value')\
            .annotate(count=Count('value'))\
            .order_by('-count')
        if size_limit is not None:
            tags = tags[:size_limit]

        try:
            # user's locale depending on language send by browser
            locale.setlocale(locale.LC_ALL, to_locale(get_language()))
        except locale.Error:
            # use the system's default locale
            locale.setlocale(locale.LC_ALL, '')

        return [{'name': tag[0],
                 'count': tag[1],
                 'size': 1 + tag[1] // (1 + tags[0][1] // 10)}
                for tag in sorted(tags, key=lambda x: locale.strxfrm(x[0]))]

    def get_randompages(self, size=10):
        """
        Get a list of random wiki articles. Redirects are excluded as well as
        everything defined in WIKI_PRIVILEGED_PAGES.
        """
        redirect_pages = [red_page.title for red_page in Page.objects.find_by_metadata('X-Redirect')]
        pagelist = [page for page
            in Page.objects.get_page_list(exclude_privileged=True)
            if page not in redirect_pages]
        size = min(size, len(pagelist))
        return random.sample(pagelist, size)

    def compare(self, name, old_rev, new_rev=None):
        """
        Compare two revisions of a page.  If the new revision is not given,
        the most recent one is taken.  The return value of this operation
        is a `Diff` instance.
        """
        if new_rev is not None:
            new_rev = int(new_rev)
        old_page = self.get_by_name_and_rev(name, int(old_rev))
        new_page = self.get_by_name_and_rev(name, new_rev)
        return Diff(old_page, old_page.rev, new_page.rev)

    def _get_object_list(self, exclude_privileged=False, exclude_pages=False, exclude_attachments=False, existing_only=True):
        """
        Get a list of all objects that are pages or attachments. It is possible
        to filter out attachments, pages, privileged or deleted/existing objects.
        """
        queryset = Page.objects.select_related('last_rev')
        if exclude_privileged:
            for name in settings.WIKI_PRIVILEGED_PAGES:
                queryset = queryset.exclude(name__istartswith=name)
        if exclude_attachments:
            queryset = queryset.exclude(last_rev__attachment__id__isnull=False)
        if exclude_pages:
            queryset = queryset.exclude(last_rev__attachment__id__isnull=True)
        if existing_only:
            queryset = queryset.exclude(last_rev__deleted=True)
        return list(queryset.values_list('name', flat=True).order_by('name'))

    def get_page_list(self, existing_only=True, cached=True, exclude_privileged=False):
        """
        Get a list of unicode strings with the page names that have a
        head that exists.  Normally the results are cached, pass it
        `cached` if you want to force the database query.  Normally this
        is not necessary because whenever a page is deleted or created the
        pagelist cache is invalidated.
        """
        kwargs = {
            'exclude_attachments': True,
            'exclude_privileged': exclude_privileged,
            'existing_only': existing_only
        }
        make_pagelist = lambda: self._get_object_list(**kwargs)

        if cached:
            key = 'wiki/objects_pages'
            if existing_only:
                key += '_existing'
            if exclude_privileged:
                key += '_without_privileged'
            return cache.get_or_set(key, make_pagelist, settings.WIKI_CACHE_TIMEOUT)

        return make_pagelist()

    def get_slug_list(self):
        """
        Returns a cached slugified list of all wiki pages, useful to speed up
        our parser a lot. Avoids many cache or db hits on big pages/texts.
        """
        make_sluglist = lambda: {wiki_slugify(name) for name in self._get_object_list(exclude_attachments=True)}
        key = 'wiki/objects_slugs'
        return cache.get_or_set(key, make_sluglist, settings.WIKI_CACHE_TIMEOUT)

    def get_attachment_list(self, parent=None, existing_only=True,
                            cached=True, exclude_privileged=False):
        """
        Works like `get_page_list` but just lists attachments.  If parent is
        given only pages below that page are displayed.
        """
        kwargs = {
            'exclude_pages': True,
            'exclude_privileged': exclude_privileged,
            'existing_only': existing_only
        }
        make_pagelist = lambda: self._get_object_list(**kwargs)

        if cached:
            key = 'wiki/objects_attachments'
            if existing_only:
                key += '_existing'
            if exclude_privileged:
                key += '_without_privileged'
            filtered = cache.get_or_set(key, make_pagelist, settings.WIKI_CACHE_TIMEOUT)
        else:
            filtered = make_pagelist()

        if parent is not None:
            parent += '/'
            parents = set(parent.split('/'))
            filtered = (x for x in filtered if x.startswith(parent) and not
                        set(x.split('/')[:-1]) - parents)
        return list(filtered)

    def discussions(self, topic):
        return Page.objects.only('name').filter(topic=topic).order_by('name')

    def get_page_count(self, existing_only=True, cached=True):
        """
        Get the number of pages.  Per default just pages with an non
        deleted head will be returned.  This in fact just counts the
        results returned by `get_page_list` because we hit the cache most
        of the time anyway.
        """
        return len(self.get_page_list(existing_only, cached))

    def get_owners(self, page_name):
        """
        Get a set of owners defined using the ``'X-Owner'`` metadata key.
        This set may include groups too and is probably just seful for the
        `get_privilege_flags` function from the `acl` module which uses it.

        Groups are prefixed with an ``'@'`` sig.-
        """
        owners = MetaData.objects.filter(page__name=page_name, key='X-Owner')\
                                 .values_list('value', flat=True)
        return set(owners)

    def get_owned(self, owners):
        """
        Return all the pages a user or some group (prefixed with ``@`` own).
        The return value will be a list of page names, not page objects.

        Reverse method of `get_owners`.
        """
        if not owners:
            return []
        pages = MetaData.objects.filter(key='X-Owner', value__in=owners)\
                                .values_list('page__name')
        return set(pages)

    def get_orphans(self):
        """
        Return a list of orphaned pages.  The return value will be a list
        of unicode strings, not the actual page object.  This ignores
        attachments!
        """
        ignore = {settings.WIKI_MAIN_PAGE}
        pages = set(self.get_page_list())
        linked_pages = set(MetaData.objects.values_list('value', flat=True)
                                           .filter(key='X-Link').all())
        redirects = set(MetaData.objects.values_list('value', flat=True)
                                        .filter(key='X-Redirect'))
        pages = (pages - linked_pages) - redirects
        return sorted(page for page in pages if page not in ignore)

    def get_missing(self):
        """
        Returns a dictonary where the keys are the names of a pages that do
        not exist and the value is a list of page objects which have a link to
        that missing page.
        """
        page_names = Page.objects.filter(last_rev__deleted=False).values('name')

        missing_pages = defaultdict(list)
        for meta in (MetaData.objects
                .filter(key='X-Link')
                .exclude(value__in=page_names)
                .select_related('page')):
            missing_pages[meta.value].append(meta.page)
        return missing_pages

    def get_similar(self, name, n=10):
        """
        Pass it a name and it will give you a list of page names with a
        similar name.  This also checks for similar attachments.
        """
        make_pagelist = lambda: self._get_object_list(exclude_privileged=False, existing_only=True)
        key = 'wiki/objects_similar'
        pagelist = cache.get_or_set(key, make_pagelist, settings.WIKI_CACHE_TIMEOUT)
        return [x[1] for x in get_close_matches(name, pagelist, n)]

    def get_by_slug(self, name):
        """
        Returns the true page name for `name` after slugification.
        """
        cache.get_or_set('wiki/page_by_slug_created', update_page_by_slug)

        return cache.get(to_page_by_slug_key(name))

    def get_by_name(self, name, cached=True, raise_on_deleted=False, exclude_privileged=False):
        """
        Return a page with the most recent revision.  This should be used
        from the view functions if no revision is defined because it sends
        just one query to get all data.

        The most recent version is additionally stored in the cache so that
        we don't hit the database for that.  Because some caching backends
        share cached objects you should not modify it unless you bypass
        the caching backend by passing `cached` = False.
        """
        if exclude_privileged and is_privileged_wiki_page(name):
            raise Page.DoesNotExist()

        cache_key = f'wiki/page/{name.lower()}'
        rev = cache.get(cache_key) if cached else None
        if rev is None:
            try:
                page = (Page.objects.select_related('last_rev__text', 'last_rev__user', 'last_rev__attachment',
                                                    'last_rev__page__last_rev__attachment')
                        .defer('last_rev__user__forum_read_status').get(name__iexact=name))
            except Page.DoesNotExist:
                # check for accents like ö, é, à
                existing = self.get_by_slug(name)
                if existing:
                    page = Page.objects.get_by_name(existing, cached, raise_on_deleted, exclude_privileged)
                    raise CaseSensitiveException(page)
                raise Page.DoesNotExist()

            rev = page.last_rev
            if cached:
                try:
                    cachetime = int(rev.page.metadata['X-Cache-Time'][0]) or None
                except (IndexError, ValueError):
                    cachetime = None
                cache.set(cache_key, rev, cachetime)

        page = rev.page
        page.rev = rev

        # If the page exists, but it has another case, raise an exception
        # with the right case.
        if rev.page.name != name:
            raise CaseSensitiveException(rev.page)

        if rev.deleted and raise_on_deleted:
            raise Page.DoesNotExist()
        return page

    def get_by_name_and_rev(self, name, rev, raise_on_deleted=False, exclude_privileged=False):
        """
        Works like `get_by_name` but selects a specific revision of a page,
        not the most recent one.  If `rev` is `None`, `get_by_name` is called.
        """
        if exclude_privileged and is_privileged_wiki_page(name):
            raise Page.DoesNotExist()
        if rev is None:
            return self.get_by_name(name, True, raise_on_deleted)
        rev = Revision.objects.select_related('page', 'user') \
                              .get(id=int(rev))
        if rev.page.name.lower() != name.lower() or \
                (rev.deleted and raise_on_deleted):
            raise Page.DoesNotExist()
        rev.page.rev = rev
        return rev.page

    def find_by_metadata(self, key, value=None):
        """
        Return a list of pages that have an entry for key with value in their
        metadata section.
        """
        kwargs = {'key': key}
        if value is not None:
            kwargs['value'] = value
        rv = [
            x.page
            for x in MetaData.objects.select_related('page').filter(**kwargs)
            if not is_privileged_wiki_page(x.page.name)
        ]
        rv.sort(key=lambda x: x.name)
        return rv

    def find_by_tag(self, tag):
        """
        Return a list of page names tagged with `tag`.
        The list will be sorted alphabetically.
        """
        pages = MetaData.objects.filter(key='tag', value=tag).order_by('page__name')\
                                .values_list('page__name', flat=True)
        return pages

    def attachment_for_page(self, page_name: str) -> Optional[str]:
        """
        Get the internal filename of the attachment attached to the page
        provided.  If the page does not exist or it doesn't have an attachment
        defined the return value will be `None`.
        """
        try:
            page = Page.objects.get_by_name(page_name)
        except Page.DoesNotExist:
            return None
        except CaseSensitiveException as e:
            page = e.page

        attachment = page.last_rev.attachment
        if not attachment:
            return None

        return attachment.file.name

    def render_all_pages(self):
        """
        This method will rerender all wiki pages (only the newest revision of them and only non-privilged ones).
        If run on a schedule, it can guarantee that an up-to-date version is in the cache.

        If a page is already in the cache, the cache entry will be dropped before rerendering it.
        """
        page_list = self.get_page_list(exclude_privileged=True)

        for name in page_list:
            try:
                page = self.get_by_name(name, exclude_privileged=True)
            except CaseSensitiveException as e:
                page = e.page
            except Page.DoesNotExist:
                continue

            if page.rev.attachment:
                # page is an attachment
                continue

            page.rev.text.remove_value_from_cache()

            logger.info(f'# Start rendering {name}')
            start = time.perf_counter()

            # as this runs normally in a celery task, prevent to spawn new celery tasks (do not use `page.rev.rendered_text`)
            page.rev.text.value_rendered[:100]

            end = time.perf_counter()
            time_delta = end - start
            logger.info(f' Finished {name}, took {time_delta} seconds')

    def create(self, name, text, user=None, change_date=None,
               note=None, attachment=None, attachment_filename=None,
               deleted=False, remote_addr=None, update_meta=True):
        """
        Create a new wiki page.  Always use this method to create pages,
        never the `Page` constructor which doesn't create the revision and
        text objects.

        :Parameters:

            name
                This must be a *normalized* version of the page name.  The
                default action dispatcher (`inyoka.wiki.views.show_page`)
                automatically normalizes incoming page names so this is no
                issue from the web layer.  However, shell scripts, converters,
                crons etc. have to normalize this parameter themselves.

            text
                Either a text object or a text that represents the text.  If
                it's a string inyoka calculates a hash of it and tries to find
                a text with the same value in the database.

            user
                If this parameter is `None` the inyoka system user will be the
                author of the created revision.  Otherwise, it can either be a
                User or an AnoymousUser object from the auth contrib module.

            change_date
                If this is not provided the current date is used.  Otherwise,
                it should be an UTC timestamp in form of a `datetime.datetime`
                object.

            note
                The change note for the revision.  If not given it will be
                ``'Created'`` or something like that.

            attachment
                see `attachment_filename`

            attachment_filename
                if an attachment filename is given the page will act as an
                attachment.  The `attachment` must be a bytestring in current
                django versions, for performance reasons latter versions
                probably will support a file descriptor here.

            deleted
                If this is `True` the page is created as a deleted page.
                This operation doesn't make sense and creates suprising
                displays in the revision log if the `note` is not changed to
                something reasonable.

            remote_addr
                The remote address of the user that created this page.  Either
                remote_addr or user is required.  This decision was made so
                that no confusion comes up when creating page objects in the
                context of a request that are not affiliated with the user.

            update_meta
                This is a boolean that defines whether metadata should be
                updated or not. It's useful to disable this for converter
                scripts.
        """
        if user is None:
            user = apps.get_model('portal', 'User').objects.get_system_user()
        elif user.is_anonymous:
            user = None
        if remote_addr is None and user is None:
            raise TypeError('either user or remote addr required')
        page = Page(name=name)
        if change_date is None:
            change_date = datetime.utcnow()
        if isinstance(text, str):
            text, created = Text.objects.get_or_create(value=text)
        if note is None:
            note = _('Created')
        if attachment is not None:
            att = Attachment()
            attachment_filename = secure_filename(attachment_filename)
            att.file.save(attachment_filename, attachment)
            att.save()
            attachment = att
        page.save()
        page.rev = Revision(page=page, text=text, user=user,
                            change_date=change_date, note=note,
                            attachment=attachment, deleted=deleted,
                            remote_addr=remote_addr)
        page.rev.save()
        page.last_rev = page.rev
        page.save()
        if update_meta:
            page.update_meta()
        return page

    def clear_topic(self, topic):
        """Unset the topic from all pages associated with it."""
        pages = Page.objects.filter(topic=topic)
        names = pages.values_list('name', flat=True)
        keys = [f'wiki/page/{n}'.lower() for n in names]
        if pages.update(topic=None) > 0:
            cache.delete_many(keys)

    def clean_cache(self, names=None):
        if names:
            if isinstance(names, str):
                names = [names, ]
            lower_names = [name.lower() for name in names]
            cache.delete_many([f'wiki/page/{name}' for name in lower_names])
            cache.delete_many([to_page_by_slug_key(name) for name in lower_names])
        cache.delete_pattern('wiki/objects_*')
        update_page_by_slug.delay()


class TextManager(models.Manager):
    """
    Helper manager for the text table so that we can get texts by the
    hash of an object.  You should always use the `get_or_create`
    function to get or create a text.  Available as `Text.objects`.
    """

    def get_or_create(self, value):
        """
        Works like a normal `get_or_create` function, just that it takes the
        value as positional argument too and that it uses a hash to find the
        correct text, rather than a string based search.
        """
        hash = sha1(value.encode('utf-8')).hexdigest()
        return models.Manager.get_or_create(self, hash=hash,
                                            defaults={'value': value})


class RevisionManager(models.Manager):
    """Helper manager for revisions"""

    def get_latest_revisions(self, page_name=None, count=10):
        revisions = self.select_related('user', 'page').defer('user__forum_read_status', 'text')

        if page_name is not None:
            revisions = revisions.filter(page__name__iexact=page_name)

        return revisions[:count]


class Diff:
    """
    This class represents the results of a page comparison.  You can get
    useful instances of this class by using the ``compare`` function on
    the `PageManager`.

    :IVariables:
        page
            The page for the old and new revision.

        old_rev
            A revision object that points to the left, not necessarily older
            revision.

        new_rev
            A revision object like for `old_rev`, but for the right and most
            likely newer revision.

        udiff
            The udiff of the diff as string.

        template_diff
            The diff in parsed form for the template.  This is mainly used by
            the ``'wiki/_diff.html'`` template which is automatically rendered
            if one calls the `render()` method on the instance.
    """

    def __init__(self, page, old, new):
        """
        This constructor exists mainly for internal usage.  It's not supported
        to create `Diff` object yourself.
        """
        self.page = page
        self.old_rev = old
        self.new_rev = new
        self.udiff = generate_udiff(old.text.value, new.text.value,
                                    '%s (%s)' % (
                                        page.name,
                                        format_datetime(old.change_date)
                                    ), '%s (%s)' % (
                                        page.name,
                                        format_datetime(new.change_date)
                                    ))
        diff = prepare_udiff(self.udiff)
        self.template_diff = diff and diff[0] or {}

    def render(self):
        """
        Render the diff using the ``wiki/_diff.html`` template.  Have a look
        at the class' docstring for more detail.
        """
        return render_to_string('wiki/_diff.html', {'diff': self})

    def __str__(self):
        return self.render()

    def __repr__(self):
        return '<%s %r - %r>' % (
            self.__class__.__name__,
            self.old_rev,
            self.new_rev
        )


class Text(models.Model):
    """
    The text for a revision.  Keep in mind that text objects are shared among
    revisions so *never ever* edit a text object after it was created.

    Because of that some methods require an explicit page object being passed
    or a `RenderContext`.

    :IVariables:

        value
            The raw unicode value of the text.

        hash
            The internal unique hash for this text.
    """
    objects = TextManager()
    value = InyokaMarkupField(application='wiki')
    hash = models.CharField(max_length=40, unique=True, db_index=True)

    # TODO: Remove this method. It is not used for the real rendering!
    def parse(self, template_context=None, transformers=None):
        """
        Parse the markup into a tree.  This also expands template code if the
        template context provided is not None.
        """
        if template_context is not None:
            value = templates.process(self.value, template_context)
        else:
            value = self.value
        return markup.parse(value, transformers=transformers)

    def find_meta(self):
        """
        Return all sort of metadata that is available on this page.  This
        includes links, commented metadata and the simplified text.
        """
        tree = self.parse()
        links = []
        metadata = []

        def walk(node):
            for child in node.children:
                if child.is_container:
                    walk(child)
                if child.__class__ is nodes.InternalLink:
                    # the leading slash enforces an absolute link.
                    links.append('/' + child.page)
                elif child.__class__ is nodes.MetaData:
                    for value in child.values:
                        metadata.append((child.key, value))
        walk(tree)

        return {
            'links': links,
            'metadata': metadata,
            'text': tree.text
        }

    def get_value_render_context_kwargs(self):
        """
        Adds additional kwargs to generate the RenderContext object.
        """
        # HACK: I don't know any other way to get the page object related to
        #       this text object. A text object could be linked to different
        #       pages, but this code does always return the page object from
        #       first revision it gets.
        return {'wiki_page': self.revisions.all()[0].page}

    def __repr__(self):
        return '<%s %r>' % (
            self.__class__.__name__,
            self.id
        )


class Page(models.Model):
    """
    This represents one wiki page and optionally also a bound revision.
    `Page` instances exist both bound and unbound.  We refer to a bound page
    when a revision was attached to the page *and* the query documents that.

    Some queries might add a revision to the page object for reasons of
    optimization.  In that case the page appears to be bound.  In such a
    situation it's unsafe to call `save()` on the page object.

    Only save pages obtained by a `PageManager.get_by_name()` or
    `PageManager.get_by_name_and_rev()`!

    :IVariables:

        name
            The normalized name of the page, as used in the URLs.
            For displaying a page's name, `page.title` should be used.
            This is guaranteed to be unique.

        topic
            A foreign key to the topic that belongs to this wiki page.

        rev
            If the page is bound this points to a `Revision` otherwise `None`.
    """
    objects = PageManager()
    name = models.CharField(max_length=200, unique=True, db_index=True)
    topic = models.ForeignKey('forum.Topic', null=True, on_delete=models.PROTECT)
    last_rev = models.ForeignKey('Revision', null=True, related_name='+', on_delete=models.CASCADE)

    #: this points to a revision if created with a query method
    #: that attaches revisions. Also creating a page object using
    #: the create() function binds the revision.
    rev = None

    @property
    def title(self):
        """
        The title of the page.  This is automatically generated from the page
        name and cannot be changed.  However future versions might support
        giving pages different titles by using the metadata system.
        """
        return get_pagetitle(self.name)

    @property
    def short_title(self):
        """
        Like `title` but just the short version of it.  Thus it returns the
        outermost part (after the last slash).  This is primarly used in the
        `do_show` action.
        """
        return get_pagetitle(self.name, full=False)

    @property
    def full_title(self):
        """Like `title` but returns the revision information too."""
        if self.rev is not None:
            return self.rev.title
        return self.title

    @property
    def trace(self):
        """The trace of pages to this page."""
        parts = get_pagetitle(self.name, full=True).split('/')
        return ['/'.join(parts[:idx + 1]) for idx in range(len(parts))]

    @deferred
    def backlinks(self):
        """List of `Page` objects that link to this page."""
        return Page.objects.find_by_metadata('X-Link', self.name)

    @deferred
    def embedders(self):
        """List of `Page` objects that embed this page as attachment."""
        return Page.objects.find_by_metadata('X-Attach', self.name)

    @deferred
    def links(self):
        """
        Internal wiki links on this page.  Because there could be links to
        non-existing pages the list returned contains just the link targets
        in normalized format, not the page objects as such.
        """
        return MetaData.objects.filter(page=self.id, key='X-Link')\
                               .values_list('value', flat=True)

    @deferred
    def metadata(self):
        """
        Get the metadata from this page as `MultiMap`.  It's not possible to
        change metadata from the model because it's an aggregated value from
        multiple sources (explicit metadata, backlinks, macros etc.)
        """
        meta = MetaData.objects.filter(page=self.id) \
                               .values_list('key', 'value')
        return MultiMap(meta)

    @property
    def is_main_page(self):
        """`True` if this is the main page."""
        return self.name == settings.WIKI_MAIN_PAGE

    def update_meta(self):
        """
        Update page metadata and crosslinks. This method always operates on the
        most recent revision, never on the revision attached to the page. If
        there is no revision in the database yet this method fails silently.

        Thus, the page create method has to call this after the revision was
        saved manually.
        """
        try:
            rev = self.revisions.latest()
        except Revision.DoesNotExist:
            return
        meta = rev.text.find_meta()

        # regular metadata and links
        new_metadata = set(meta['metadata'])

        for key, value in new_metadata:
            if key == 'X-Behave':
                from inyoka.wiki.storage import storage
                storage.clear_cache()
                break

        # add links as x-links
        new_metadata.update(('X-Link', link) for link in meta['links'])

        # make links and attachment targets absolute
        for t in list(new_metadata):
            key, value = t
            if key in ('X-Link', 'X-Attach'):
                if t in new_metadata:
                    new_metadata.remove(t)
                new_metadata.add((key, join_pagename(self.name, value)))

        qs = MetaData.objects.filter(page=self.id) \
                             .values_list('id', 'key', 'value')
        to_remove = []

        for id, key, value in qs:
            item = (key, value)
            if item in new_metadata:
                new_metadata.remove(item)
            else:
                to_remove.append(id)

        if to_remove:
            MetaData.objects.filter(id__in=to_remove).delete()

        for key, value in new_metadata:
            # ignore keys that do not fetch into the column length.
            # Most commonly such metadata entries are broken comments...
            if len(key) > 30:
                continue
            MetaData(page=self, key=key, value=value[:MAX_METADATA]).save()

    def save(self, update_meta=True, *args, **kwargs):
        """
        This not only saves the page but also a revision that is
        bound to the page object.  If you don't want to save the
        revision set it to `None` before calling `save()`.
        """
        if self.id is None:
            Page.objects.clean_cache()
        models.Model.save(self)
        if self.rev is not None:
            self.rev.save()
        deferred.clear(self)
        # FIXME: We are using apply_async() instead of delay() because there is
        #        a real dumb race condition between the celery task and this save().
        update_related_pages.apply_async(args=[self.pk, update_meta], countdown=5)

    def delete(self):
        """
        This simply raises an exception, as we never want to delete pages really.
        Instead we just mark pages as deleted, which is done with edit(deleted=True).

        The purpose of this method is to avoid using the django default delete() and
        avoid some side effects with it.
        """
        raise NotImplementedError('Please use edit(deleted=True) instead.')

    def edit(self, text=None, user=None, change_date=None,
             note='', attachment=None, attachment_filename=None,
             deleted=None, remote_addr=None, update_meta=True,
             clean_cache=True):
        """
        This saves outstanding changes and creates a new revision which is
        then attached to the `rev` attribute.

        :Parameters:

            text
                Either a text object or a text that represents the text.  If
                it's a string inyoka calculates a hash of it and tries to find
                a text with the same value in the database.  If no text is
                provided the text from the last revision is used.

            user
                If this parameter is `None` the inyoka system user will be the
                author of the created revision.  Otherwise, it can either be a
                User or an AnonymousUser object from the auth contrib module.

            change_date
                If this is not provided the current date is used.  Otherwise,
                it should be an UTC timestamp in form of a `datetime.datetime`
                object.

            note
                The change note for the revision.  If not given it will be
                empty.

            attachment
                see `attachment_filename`

            attachment_filename
                if an attachment filename is given the page will act as an
                attachment.  The `attachment` must be a bytestring in current
                django versions, for performance reasons later versions
                probably will support a file descriptor here.  If no
                attachment filename is given the page will either continue to
                be a page or attachment depending on the last revision.

            deleted
                If this is `True` the page is created as a deleted page.
                This operation doesn't make sense and creates surprising
                displays in the revision log if the `note` is not changed to
                something reasonable.

            remote_addr
                The remote address of the user that created this page.  If not
                given it will be None but either remote_addr or user has to
                be present.  This decision was made so that no confusion comes
                up when creating page objects in the context of a request that
                are not affiliated with the user.

            update_meta
                This is a boolean that defines whether metadata should be
                updated or not. It's useful to disable this for converter
                scripts.
        """
        if user is None:
            user = apps.get_model('portal', 'User').objects.get_system_user()
        elif user.is_anonymous:
            user = None

        if remote_addr is None and user is None:
            raise TypeError('either user or remote addr required')

        try:
            rev = self.revisions.latest()
        except Revision.DoesNotExist:
            rev = None

        if deleted is None:
            if rev:
                deleted = rev.deleted
            else:
                deleted = False

        if deleted:
            text = ''

        if text is None:
            text = rev and rev.text or ''

        if isinstance(text, str):
            text, created = Text.objects.get_or_create(value=text)

        if attachment_filename is None:
            attachment = rev and rev.attachment or None
        elif attachment is not None:
            att = Attachment()
            attachment_filename = secure_filename(attachment_filename)
            att.file.save(attachment_filename, attachment)
            att.save()
            attachment = att

        if change_date is None:
            change_date = datetime.utcnow()

        self.rev = Revision(page=self, text=text, user=user,
                            change_date=change_date, note=note,
                            attachment=attachment, deleted=deleted,
                            remote_addr=remote_addr)
        self.rev.save()
        self.last_rev = self.rev
        self.save(update_meta=update_meta)

        if clean_cache:
            Page.objects.clean_cache(self.name)

    def get_absolute_url(self, action='show', revision=None, new_revision=None,
                         format=None, **query):
        actions = ('attachments',
                   'backlinks',
                   'delete',
                   'discussion',
                   'edit',
                   'feed',
                   'log',
                   'mv_back',
                   'mv_baustelle',
                   'mv_discontinued',
                   'rename',
                   'subscribe',
                   'unsubscribe')

        action_href = partial(href, 'wiki', self.name, 'a')

        if action in actions:
            return action_href(action, **query)
        elif action == 'diff' or action == 'udiff':
            if revision is None and new_revision is None:
                return action_href(action)
            elif new_revision is None:
                return action_href(action, revision)
            else:
                return action_href(action, revision, new_revision)
        elif action == 'show_no_redirect':
            return href('wiki', self.name, 'no_redirect', **query)
        elif action == 'revert' and revision is not None:
            return action_href('revert', revision, **query)
        elif action == 'export' and format is not None:
            if revision is not None:
                return action_href('export', format, revision, **query)
            else:
                return action_href('export', format, **query)
        elif revision is not None:
            return action_href('revision', revision, **query)
        else:
            return href('wiki', self.name, **query)

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<%s %r%s>' % (
            self.__class__.__name__,
            self.name,
            self.rev and ' rev %r' % self.rev.id or ''
        )

    class Meta:
        ordering = ['name']
        verbose_name = gettext_lazy('Wiki page')
        verbose_name_plural = gettext_lazy('Wiki pages')
        indexes = [
            models.Index(Upper('name'), name='upper_page_name_idx'),
        ]


class Attachment(models.Model):
    """
    Revisions can have uploaded data associated, this table holds the
    mapping to the uploaded file on the file system.
    """
    file = models.FileField(upload_to='wiki/attachments/%S/%W')

    @property
    def size(self):
        """The size of the attachment in bytes."""
        return self.file.size()

    @property
    def filename(self):
        """The filename of the attachment on the filesystem."""
        return self.file.path

    @cached_property
    def mimetype(self):
        """The mimetype of the attachment."""
        return magic.from_file(self.file.path, mime=True) or \
            'application/octet-stream'

    @property
    def contents(self):
        """
        The raw contents of the file.  This is usually unsafe because
        it can cause the memory limit to be reached if the file is too
        big.  However this limitation currently affects the whole django
        system which handles uploads in the memory.
        """
        f = self.open()
        try:
            return f.read()
        finally:
            f.close()

    @property
    def html_representation(self):
        """
        This method returns a `HTML` representation of the attachment for the
        `show_action` page.  If this method does not know about an internal
        representation for the object the return value will be an download
        link to the raw attachment.
        """
        url = escape(self.get_absolute_url())
        if self.mimetype.startswith('image/'):
            return '<a href="%s"><img class="attachment" src="%s" ' \
                   'alt="%s"></a>' % (url, url, url)
        else:
            code = ''
            if self.mimetype.startswith('text/'):
                code = highlight_code(self.contents, filename=self.filename)
            return '%s<a href="%s">%s</a>' % (code, url, _('Download attachment'))

    def open(self, mode='rb'):
        """
        Open the file as file descriptor.  Don't forget to close this file
        descriptor accordingly.
        """
        self.file.open(mode)
        return self.file

    def get_absolute_url(self, action=None):
        return self.file.url


class Revision(models.Model):
    """
    Represents a single page revision.  A revision object is always bound to
    a page which is available with the `page` attribute.

    Most of the time `Revision` objects appear as a part of a `Page` object
    for some `actions` however they enter a template context without a page
    object too.

    :IVariables:

        page
            The page this object is operating on.  In the templates however
            you will never have to access this attribute because all revisions
            sent to the template are either part of a bound `Page` or provide
            an extra object for the page itself.

        text
            a `Text` object.  In templates you usually don't have to cope with
            this attribute because it just contains the raw data and not the
            rendered one.  For the rendered data have a look at
            `rendered_text`.

        user
            The user that created this revision.  If an anoymous user created
            the revision this will be `None`.

        change_date
            The date of the revision as `datetime.datetime` object.

        note
            The change note as string.

        deleted
            If the revision is marked as deleted this is `True`.

        remote_addr
            The remote address for the user.  In templates this is a useful
            attribute if you need a replacement for the `user` when no user is
            present.

        attachment
            If the page itself holds an attachment this will point to an
            `Attachment` object.  Otherwise this attribute is `None` and must
            be ignored.
    """
    objects = RevisionManager()
    page = models.ForeignKey(Page, related_name='revisions', on_delete=models.CASCADE)
    text = models.ForeignKey(Text, related_name='revisions', on_delete=models.CASCADE)
    user = models.ForeignKey('portal.User', related_name='wiki_revisions',
                             null=True, blank=True, on_delete=models.CASCADE)
    change_date = models.DateTimeField(db_index=True)
    note = models.CharField(max_length=512)
    deleted = models.BooleanField(default=False)
    remote_addr = models.CharField(max_length=200, null=True)
    attachment = models.ForeignKey(Attachment, null=True, blank=True, on_delete=models.CASCADE)

    @property
    def title(self):
        """
        The page title plus the revision date.  This is equivalent to
        `Page.full_title`.
        """
        return _('%(rev)s (Revision %(date)s)' % {
            'rev': self.page.title,
            'date': format_datetime(self.change_date)
        })

    @property
    def rendered_text(self):
        """
        The rendered version of the `text` attribute.

        If the page is not in the cache yet, schedule a (semi-parallel) celery task.

        Reason: Some Inyoka markup renders too slow to render synchronisly
        inside the request and will display a timeout (HTTP 502).
        In those cases, the celery task will render it asynchronisly and put
        the result in the cache. As a side effect, the 502 will be displayed
        some minutes until the rendered page is in the cache.
        If the rendering finished inside the request already, the celery task
        will fetch the rendered content from the cache.
        (This is a small amount of 'wasted' work)
        To prevent rendering in parallel, the celery task should be executed
        after the gunicorn timeout, which is 30 seconds by default.
        """
        in_cache, _ = self.text.is_value_in_cache()
        if not in_cache:
            render_one_revision.apply_async(args=[self.pk], countdown=35)

        return self.text.value_rendered

    @property
    def short_description(self):
        """
        Returns a short, stripped excerpt from the beginning of the article.
        """
        excerpt = striptags(self.rendered_text)
        # search for space to not break up single words
        pos = excerpt.find(' ', 200)
        return excerpt[:pos]

    def get_absolute_url(self, action=None):
        return href('wiki', self.page.name, 'a', 'revision', self.id)

    def revert(self, note=None, user=None, remote_addr=None):
        """Revert this revision and make it the current one."""
        # no relative date information, because it stays in the note forever

        note = _('%(note)s [Revision from %(date)s restored by %(user)s]' %
            {'note': note,
             'date': datetime_to_timezone(self.change_date).strftime(
                '%d.%m.%Y %H:%M %Z'),
             'user': self.user.username if self.user else self.remote_addr})
        new_rev = Revision(page=self.page, text=self.text,
                           user=(user if user.is_authenticated else None),
                           change_date=datetime.utcnow(),
                           note=note, deleted=False,
                           remote_addr=remote_addr or '127.0.0.1',
                           attachment=self.attachment)
        new_rev.save()
        self.page.last_rev = new_rev
        self.page.save()
        return new_rev

    def save(self, *args, **kwargs):
        """Save the revision and invalidate the cache."""
        models.Model.save(self, *args, **kwargs)

        cache.delete(f'wiki/page/{self.page.name.lower()}')

    def __str__(self):
        return _('Revision %(id)d (%(title)s)') % {
            'id': self.id, 'title': self.page.title
        }

    def __repr__(self):
        return '<%s %r rev %r>' % (
            self.__class__.__name__,
            self.page.name,
            self.id
        )

    class Meta:
        get_latest_by = 'change_date'
        ordering = ['-change_date']


class MetaData(models.Model):
    """
    Every page (just pages not revisions) can have an unlimited number
    of metadata associated with.  Metadata is useful to add invisible
    information to pages such as tags, acls etc.

    This should be considered being a private class because it is wrapped
    by the `Page.metadata` property and the `Page.update_meta` method.
    """
    page = models.ForeignKey(Page, on_delete=models.CASCADE)
    key = models.CharField(max_length=30, db_index=True)
    value = models.CharField(max_length=255, db_index=True)
