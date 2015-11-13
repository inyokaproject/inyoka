# -*- coding: utf-8 -*-
"""
    inyoka.wiki.tasks
    ~~~~~~~~~~~~~~~~~

    Module that implements wiki related tasks that must be executed by
    our distributed queue implementation.

    :copyright: (c) 2007-2015 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from collections import OrderedDict
from datetime import datetime, timedelta

from celery import shared_task
from django.conf import settings
from django.core.cache import cache


@shared_task
def render_article(page):
    cache.delete('wiki/page/{}'.format(page.name.lower()))


@shared_task
def update_related_pages(page, update_meta=True):
    from inyoka.wiki.models import MetaData
    related_pages = set()
    values = ('value', 'page__last_rev__text_id')
    linked = MetaData.objects.values_list(*values) \
                     .filter(key__in=('X-Link', 'X-Attach'), value=page.name)
    for value, text_id in linked.all():
        cache.delete('wiki/page/{}'.format(value.lower()))
        related_pages.add(text_id)
    cache.delete('wiki/page/{}'.format(page.name.lower()))

    if update_meta:
        page.update_meta()


@shared_task
def update_object_list(names=None):
    """Refresh the wiki/object_list cache key"""
    from inyoka.wiki.models import Page
    if isinstance(names, list):
        cache.delete_many(['wiki/page/{}'.format(name.lower()) for name in names])
    elif isinstance(names, basestring):
        cache.delete('wiki/page/{}'.format(names.lower()))

    cache.delete('wiki/object_list')
    Page.objects.get_page_list()


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
        change_time = revision.change_date.time()
        page_name = revision.page.name
        username = revision.user.username if revision.user else None
        if change_date not in recentchanges:
            recentchanges[change_date] = OrderedDict()
        if revision.page.name not in recentchanges[change_date]:
            recentchanges[change_date][page_name] = []
        recentchanges[change_date][page_name].append({'time': change_time, 'username': username, 'note': revision.note})
    cache.set('wiki/recentchanges', recentchanges)
