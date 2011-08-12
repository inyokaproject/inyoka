# -*- coding: utf-8 -*-
"""
    inyoka.ikhaya.legacyurls
    ~~~~~~~~~~~~~~~~~~~~~~~

    Ikhaya legacy URL support.

    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
#from inyoka.forum.models import Forum, Topic
from inyoka.utils.urls import href
from inyoka.utils.legacyurls import LegacyDispatcher
from inyoka.ikhaya.models import Category


legacy = LegacyDispatcher()
test_legacy_url = legacy.tester


@legacy.url('^/archive/(\d+)/(\d+)/?$')
def archive(args, match, year, month):
    return href('ikhaya', year, month)


@legacy.url('^/category/(\d+)/?$')
def category(args, match, category_id):
    try:
        category = Category.objects.get(id=int(category_id))
    except Category.DoesNotExist:
        return
    return href('ikhaya', 'category', category.slug)


@legacy.url('^/suggest/?$')
def suggest(args, match):
    return href('ikhaya', 'suggest', 'new')
