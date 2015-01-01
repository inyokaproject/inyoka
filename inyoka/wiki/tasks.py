#-*- coding: utf-8 -*-
"""
    inyoka.wiki.tasks
    ~~~~~~~~~~~~~~~~~

    Module that implements wiki related tasks that must be executed by
    our distributed queue implementation.

    :copyright: (c) 2007-2015 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.core.cache import cache

from celery.task import task


@task(ignore_result=True)
def render_article(page):
    page.last_rev.text.update_html_render_instructions()
    cache.delete('wiki/page/%s' % page.name)


@task(ignore_result=True)
def update_related_pages(page, update_meta=True):
    from inyoka.wiki.models import MetaData, Text
    related_pages = set()
    values = ('value', 'page__last_rev__text_id')
    linked = MetaData.objects.values_list(*values) \
                     .filter(key__in=('X-Link', 'X-Attach'), value=page.name)
    for value, text_id in linked.all():
        cache.delete('wiki/page/%s' % value)
        related_pages.add(text_id)
    cache.delete('wiki/page/%s' % page.name)

    Text.objects.filter(id__in=related_pages) \
                .update(html_render_instructions=None)

    if update_meta:
        page.update_meta()


@task(ignore_result=True)
def update_object_list(names=None):
    """Refresh the wiki/object_list cache key"""
    from inyoka.wiki.models import Page
    if isinstance(names, list):
        cache.delete_many(['wiki/page/%s' % name for name in names])
    elif isinstance(names, basestring):
        cache.delete('wiki/page/%s' % names)

    cache.delete('wiki/object_list')
    Page.objects.get_page_list()
