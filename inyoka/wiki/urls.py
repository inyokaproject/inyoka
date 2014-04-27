# -*- coding: utf-8 -*-
"""
    inyoka.wiki.urls
    ~~~~~~~~~~~~~~~~

    URL list for the wiki.

    :copyright: (c) 2007-2014 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from django.conf.urls import patterns

urlpatterns = patterns('inyoka.wiki.views',
    (r'^$', 'index'),
    (r'^_image$', 'get_image_resource'),
    (r'^_newpage$', 'redirect_new_page'),
    (r'^_attachment$', 'get_attachment'),
    (r'^_feed/(?P<count>\d+)', 'feed'),
    (r'^_feed/(?P<page_name>.+)/(?P<count>\d+)', 'feed'),
    (r'^(.+?)$', 'show_page')
)


handler404 = 'inyoka.wiki.views.missing_resource'
require_trailing_slash = False
