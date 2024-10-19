"""
    inyoka.wiki.views
    ~~~~~~~~~~~~~~~~~

    The views for the wiki.  Unlike the other applications the wiki doesn't
    really use the views but `actions`.  This is the case because we only
    have one kind of page which is a wiki page.  Non existing pages render
    a replacement message to create one, so not much to dispatch.

    Some internal functions such as the image serving are implemented as
    views too because they do not necessarily work on page objects.


    :copyright: (c) 2007-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import os
from hashlib import sha1
from urllib.parse import urljoin

from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseRedirect
from django.utils.encoding import force_str
from django.utils.html import escape
from django.utils.translation import gettext as _

from inyoka.utils.dates import _localtime
from inyoka.utils.feeds import InyokaAtomFeed
from inyoka.utils.http import templated
from inyoka.utils.imaging import get_thumbnail
from inyoka.utils.text import join_pagename, normalize_pagename
from inyoka.utils.urls import href, is_safe_domain, url_for
from inyoka.wiki.acl import has_privilege
from inyoka.wiki.models import Page, Revision


def index(request):
    """Wiki index is a redirect to the `settings.WIKI_MAIN_PAGE`."""
    return HttpResponseRedirect(
        href('wiki', settings.WIKI_MAIN_PAGE) +
        (request.GET and '?' + request.GET.urlencode() or '')
    )


def redirect_new_page(request):
    """Helper for the `NewPage` macro."""
    template = request.GET.get('template')
    base = request.GET.get('base', '')
    page = request.GET.get('page', '')
    options = {'action': 'edit'}
    backref = request.headers.get('referer')
    if not backref or not is_safe_domain(backref):
        backref = href('wiki', settings.WIKI_MAIN_PAGE)

    if not page:
        messages.error(request, _('A site name needs to be entered to create this page.'))
        return HttpResponseRedirect(backref)
    if base:
        page = join_pagename(base, "./" + page)
    try:
        page = Page.objects.get(name__iexact=page)
    except Page.DoesNotExist:
        if template:
            options['template'] = join_pagename(settings.WIKI_TEMPLATE_BASE,
                                                template)
        return HttpResponseRedirect(href('wiki', page, **options))
    messages.error(request, _('Another site named “%(title)s” already exists.')
        % {'title': escape(page.title)})
    return HttpResponseRedirect(backref)


def get_attachment(request):
    """
    Get an attachment directly and do privilege check.
    """
    target = request.GET.get('target')
    if not target:
        raise Http404()

    target = normalize_pagename(target)
    if not has_privilege(request.user, target, 'read'):
        raise PermissionDenied

    target = Page.objects.attachment_for_page(target)
    target = href('media', target)
    if not target:
        raise Http404()
    return HttpResponseRedirect(target)


def fetch_real_target(target, width=None, height=None, force=False):
    """Return the uri to a image"""

    if height or width:
        page_filename = Page.objects.attachment_for_page(target)
        if page_filename is None:
            return

        page_filename = force_str(page_filename).encode('utf-8')
        partial_hash = sha1(page_filename).hexdigest()

        dimension = '%sx%s%s' % (width or '',
                                 height or '',
                                 force and '!' or '')
        hash = '%s%s%s' % (partial_hash, 'i',
                           dimension.replace('!', 'f'))
        base_filename = os.path.join('wiki', 'thumbnails', hash[:1],
                                     hash[:2], hash)
        thumbnail = get_thumbnail(page_filename.decode(), base_filename, width, height, force)

        target = urljoin(settings.MEDIA_URL, thumbnail)
    else:
        target = Page.objects.attachment_for_page(target)
        if not target:
            return None
        target = href('media', target)
    if not target:
        return None
    return target


def get_image_resource(request):
    """
    Deliver the attachment  as image.  This is used by the `Picture` macro
    mainly.  The idea is that we can still check privileges
    and that the image URL does not change if a new revision is uploaded.
    """
    target = request.GET.get('target')
    if not target:
        raise Http404()

    target = normalize_pagename(target)
    if not has_privilege(request.user, target, 'read'):
        raise PermissionDenied

    try:
        width = int(request.GET['width'])
    except (KeyError, ValueError):
        width = None
    try:
        height = int(request.GET['height'])
    except (KeyError, ValueError):
        height = None

    force = request.GET.get('force') == 'yes'
    target = fetch_real_target(target, width=width, height=height, force=force)
    if target is None:
        raise Http404()

    return HttpResponseRedirect(target)


class WikiAtomFeed(InyokaAtomFeed):
    """
    Atom feed with revisions of the *whole wiki*.
    """
    name = 'wiki_feed'
    supports_modes = False

    title = _('%(sitename)s wiki – last changes') % {'sitename': settings.BASE_DOMAIN_NAME}

    def _subtitle(self, __):
        return _('Feed contains revisions of the whole wiki')

    def link(self, *args):
        return href('wiki', 'wiki', 'recentchanges')

    def items(self, *args):
        return Revision.objects.get_latest_revisions(count=self.count)

    def item_title(self, rev):
        return '%s: %s' % (
            rev.user or settings.ANONYMOUS_USER_NAME,
            rev.note or _('-')
        )

    def item_comments(self, rev):
        return rev.page.get_absolute_url(action='discussion')

    def item_categories(self, rev):
        return rev.page.metadata['tag']

    def item_description(self, rev):
        if rev.deleted:
            text = _('%(user)s deleted the article “%(article)s” on '
                     '%(date)s. Summary: %(summary)s')
        else:
            text = _('%(user)s edited the article “%(article)s” on '
                     '%(date)s. Summary: %(summary)s')

        return text % {
            'user': rev.user or _('An anonymous user'),
            'article': rev.page.title,
            'date': _localtime(rev.change_date),
            'summary': rev.note or _('-'),
        }

    def item_link(self, rev):
        return url_for(rev)

    def item_author_name(self, rev):
        if rev.user:
            return rev.user.username

        return settings.ANONYMOUS_USER_NAME

    def item_author_link(self, rev):
        if rev.user:
            return url_for(rev.user)

        return None

    def item_pubdate(self, rev):
        return _localtime(rev.change_date)

    def item_updateddate(self, rev):
        return _localtime(rev.change_date)


class WikiPageAtomFeed(WikiAtomFeed):
    """
    Atom feed with revisions of *one wiki page*.
    """

    def title(self, page):
        return _('%(sitename)s wiki – %(pagename)s') % {
            'sitename': settings.BASE_DOMAIN_NAME,
            'pagename': page.name
        }

    def _subtitle(self, page):
        return _('Feed contains revisions of the wiki page “%(pagename)s”.') % {'pagename': page.name}

    def link(self, page):
        return page.get_absolute_url()

    def get_object(self, request, *args, **kwargs):
        super().get_object(request, *args, **kwargs)
        return Page.objects.get_by_name(kwargs['page_name'], exclude_privileged=True)

    def items(self, page):
        return Revision.objects.get_latest_revisions(page.name, self.count)


@templated('wiki/recentchanges.html')
def recentchanges(request):
    """
    Show a table of the recent changes.
    """
    return {'recentchanges': cache.get('wiki/recentchanges')}


@templated('wiki/missingpages.html')
def missingpages(request):
    """
    Show a table of links to missing pages and where they are located.
    """
    return {'missingpages': Page.objects.get_missing()}


@templated('wiki/randompages.html')
def randompages(request):
    """
    Show a list of random wiki articles.
    """
    return {'randompages': Page.objects.get_randompages()}


@templated('wiki/tag_list.html')
def show_tag_list(request):
    """
    Show an alphabetical tag list with all wiki tags.
    """
    return {'tag_list': Page.objects.get_taglist()}


@templated('wiki/tag_cloud.html')
def show_tag_cloud(request):
    """
    Show a tag cloud of the 100 most used tags.
    """
    return {'tag_list': Page.objects.get_taglist(settings.TAGCLOUD_SIZE)}


@templated('wiki/pages_by_tag.html')
def show_pages_by_tag(request, tag):
    """
    Show a list of wiki pages that are tagged with
    the specified key word.
    """
    page_list = Page.objects.find_by_tag(tag)
    if not page_list:
        raise Http404()
    return {
        'page_list': page_list,
        'active_tag': tag
    }
