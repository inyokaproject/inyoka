"""
    inyoka.wiki.tasks
    ~~~~~~~~~~~~~~~~~

    Module that implements wiki related tasks that must be executed by
    our distributed queue implementation.

    :copyright: (c) 2007-2023 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from collections import OrderedDict
from datetime import datetime, timedelta
from os import path, remove

from celery import shared_task
from django.conf import settings
from django.core.cache import cache

from inyoka.utils.logger import logger


@shared_task
def cleanup_stale_attachments():
    """
    Sometimes our database has Attachment objects not referenced by any Page
    or Revision. This tasks detect these stale objects and delete the file from
    the filesystem itself.

    As a benefit we must never delete these files in any view or model.
    """
    from inyoka.wiki.models import Attachment

    orphan_attachments = Attachment.objects.filter(revision__attachment__id=None)

    logger.info('Deleting %s stale wiki attachments…' % len(orphan_attachments))

    for attachment in orphan_attachments:
        filename = path.join(settings.MEDIA_ROOT, attachment.file.name)
        if path.isfile(filename):
            remove(filename)

        attachment.delete()


@shared_task
def update_page_by_slug():
    """
    Updates the mapping between wiki slugs and the real page names, should run
    from time to time to avoid in-request processing for this mapping.
    """
    from inyoka.wiki.models import Page, to_page_by_slug_key as to_key

    # This sets only the canary, so we don't run more than once at a time.
    cache.set('wiki/page_by_slug_created', True)

    for page_name in Page.objects._get_object_list(exclude_attachments=True):
        cache.set(to_key(page_name), page_name, settings.WIKI_CACHE_TIMEOUT)

    # We also return True here, so calls through get_or_set() won't set our
    # canary to a different value.
    return True


@shared_task
def update_related_pages(page, update_meta=True):
    from inyoka.wiki.models import MetaData, Page
    page = Page.objects.get(id=page)
    related_pages = set()
    values = ('value', 'page__last_rev__text_id')
    linked = MetaData.objects.values_list(*values) \
                     .filter(key__in=('X-Link', 'X-Attach'), value=page.name)
    for value, text_id in linked.all():
        cache.delete(f'wiki/page/{value.lower()}')
        related_pages.add(text_id)
    cache.delete(f'wiki/page/{page.name.lower()}')

    if update_meta:
        page.update_meta()


@shared_task
def update_recentchanges():
    """
    Updates cached data for recent changes View.
    """
    from inyoka.wiki.models import Revision

    from_time = datetime.utcnow() - timedelta(days=settings.WIKI_RECENTCHANGES_DAYS)

    revisions = (Revision.objects
        .filter(change_date__gt=from_time)
        .order_by('-change_date')
        .select_related('user', 'page')[:settings.WIKI_RECENTCHANGES_MAX])

    recentchanges = OrderedDict()
    for revision in revisions:
        change_date = revision.change_date.date()
        page_name = revision.page.name
        username = revision.user.username if revision.user else None
        if change_date not in recentchanges:
            recentchanges[change_date] = OrderedDict()
        if revision.page.name not in recentchanges[change_date]:
            recentchanges[change_date][page_name] = []
        recentchanges[change_date][page_name].append(
            {
                'change_date': revision.change_date,
                'username': username,
                'note': revision.note
            })
    cache.set('wiki/recentchanges', recentchanges)


@shared_task
def render_all_pages():
    """
    Prerenders all wiki pages.
    """
    from inyoka.wiki.models import Page
    Page.objects.render_all_pages()


@shared_task
def render_one_revision(revision_id: int):
    from inyoka.wiki.models import Revision
    Revision.objects.get(id=revision_id).rendered_text[:100]
