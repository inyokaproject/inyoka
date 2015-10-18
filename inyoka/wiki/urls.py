# -*- coding: utf-8 -*-
"""
    inyoka.wiki.urls
    ~~~~~~~~~~~~~~~~

    URL list for the wiki.

    :copyright: (c) 2007-2015 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.conf import settings
from django.conf.urls import include, patterns, url

urlpatterns = patterns('inyoka.wiki.views',
    (r'^$', 'index'),
    (r'^_image$', 'get_image_resource'),
    (r'^_newpage$', 'redirect_new_page'),
    (r'^_attachment$', 'get_attachment'),
    (r'^_feed/(?P<count>\d+)', 'feed'),
    (r'^_feed/(?P<page_name>.+)/(?P<count>\d+)', 'feed'),
    (r'^wiki/recentchanges', 'recentchanges'),
    (r'^wiki/tags$', 'show_tag_list'),
    (r'^wiki/tags/(?P<tag>.+)', 'show_pages_by_tag')
)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += patterns('',
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )

urlpatterns += patterns('inyoka.wiki.views',
    (r'^(.+?)$', 'show_page')
)

handler404 = 'inyoka.utils.http.global_not_found'
require_trailing_slash = False
