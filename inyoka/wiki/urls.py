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
    (r'^_feed/(?P<count>\d+)/?$', 'feed'),
    (r'^(?P<page_name>.+)/a/feed/?$', 'feed', {'count': 10}),
    (r'^(?P<page_name>.+)/a/feed/(?P<count>\d+)/?$', 'feed'),
    (r'(?i)^wiki/recentchanges', 'recentchanges'),
    (r'(?i)^wiki/tagcloud$', 'show_tag_cloud'),
    (r'(?i)^wiki/tags$', 'show_tag_list'),
    (r'(?i)^wiki/tags/(?P<tag>.+)', 'show_pages_by_tag')
    )

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += patterns('',
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )

urlpatterns += patterns('inyoka.wiki.actions',
    (r'(?i)^wiki/create/?$', 'do_create'),
    (r'(?i)^wiki/create/(?P<name>.+)/?$', 'do_create'),
    (r'^(?P<name>.+)/a/attachments/?$', 'do_attach'),
    (r'^(?P<name>.+)/a/backlinks/?$', 'do_backlinks'),
    (r'^(?P<name>.+)/a/delete/?$', 'do_delete'),
    (r'^(?P<name>.+)/a/diff/?$', 'do_diff'),
    (r'^(?P<name>.+)/a/diff/(?P<old_rev>\d+)/(?P<new_rev>\d+)/?$', 'do_diff'),
    (r'^(?P<name>.+)/a/discussion/?$', 'do_manage_discussion'),
    (r'^(?P<name>.+)/a/edit/?$', 'do_edit'),
    (r'^(?P<name>.+)/a/edit/revision/(?P<rev>\d+)/?$', 'do_edit'),
    (r'^(?P<name>.+)/a/export/(?P<format>(raw|html|ast))/?$', 'do_export'),
    (r'^(?P<name>.+)/a/export/(?P<format>(raw|html|ast))/fragment/?$', 'do_export', {'fragment': True}),
    (r'^(?P<name>.+)/a/export/(?P<format>(raw|html|ast))/(?P<rev>\d+)/?$', 'do_export'),
    (r'^(?P<name>.+)/a/export/(?P<format>(raw|html|ast))/(?P<rev>\d+)/fragment/?$', 'do_export', {'fragment': True}),
    (r'^(?P<name>.+)/a/export/meta/?$', 'do_metaexport'),
    (r'^(?P<name>.+)/a/log/(?P<pagination_page>\d+)/?$', 'do_log'),
    (r'^(?P<name>.+)/a/log/?$', 'do_log'),
    (r'^(?P<name>.+)/a/mv_back/?$', 'do_mv_back'),
    (r'^(?P<name>.+)/a/mv_baustelle/?$', 'do_mv_baustelle'),
    (r'^(?P<name>.+)/a/mv_discontinued/?$', 'do_mv_discontinued'),
    (r'^(?P<name>.+)/a/rename/?$', 'do_rename'),
    (r'^(?P<name>.+)/a/rename/force/?$', 'do_rename', {'force': True}),
    (r'^(?P<name>.+)/a/revert/(?P<rev>\d+)/?$', 'do_revert'),
    (r'^(?P<name>.+)/a/revision/(?P<rev>\d+)/?$', 'do_show'),
    (r'^(?P<name>.+)/a/revision/(?P<rev>\d+)/no_redirect/?$', 'do_show', {'allow_redirect': False}),
    (r'^(?P<name>.+)/a/subscribe/?$', 'do_subscribe'),
    (r'^(?P<name>.+)/a/udiff/?$', 'do_diff', {'udiff': True}),
    (r'^(?P<name>.+)/a/udiff/(?P<old_rev>\d+)/(?P<new_rev>\d+)/?$', 'do_diff', {'udiff': True}),
    (r'^(?P<name>.+)/a/unsubscribe/?$', 'do_unsubscribe'),
    (r'^(?P<name>.+)/no_redirect/?$', 'do_show', {'allow_redirect': False}),
    (r'^(?P<name>.+)/?$', 'do_show'),
    )

handler404 = 'inyoka.utils.http.global_not_found'
require_trailing_slash = False
