# -*- coding: utf-8 -*-
"""
    inyoka.wiki.urls
    ~~~~~~~~~~~~~~~~

    URL list for the wiki.

    :copyright: (c) 2007-2023 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.conf import settings
from django.conf.urls import include, url

from . import actions, views
from ..utils.http import global_not_found, server_error

urlpatterns = [
    url(r'^$', views.index),
    url(r'^_image/$', views.get_image_resource),
    url(r'^_newpage/$', views.redirect_new_page),
    url(r'^_attachment/$', views.get_attachment),
    url(r'^_feed/(?P<count>\d+)/$', views.feed),
    url(r'^(?P<page_name>.+)/a/feed/$', views.feed, {'count': 10}),
    url(r'^(?P<page_name>.+)/a/feed/(?P<count>\d+)/$', views.feed),
    url(r'^wiki/recentchanges/$', views.recentchanges),
    url(r'^wiki/missingpages/$', views.missingpages),
    url(r'^wiki/randompages/$', views.randompages),
    url(r'^wiki/tagcloud/$', views.show_tag_cloud),
    url(r'^wiki/tags/$', views.show_tag_list),
    url(r'^wiki/tags/(?P<tag>.+)/$', views.show_pages_by_tag)
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns.append(
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )

urlpatterns.extend([
    url(r'^wiki/create/?$', actions.do_create),
    url(r'^wiki/create/(?P<name>.+)/$', actions.do_create),
    url(r'^(?P<name>.+)/a/attachments/$', actions.do_attach),
    url(r'^(?P<name>.+)/a/backlinks/$', actions.do_backlinks),
    url(r'^(?P<name>.+)/a/delete/$', actions.do_delete),
    url(r'^(?P<name>.+)/a/diff/(?P<old_rev>\d+)/(?P<new_rev>\d+)/$', actions.do_diff),
    url(r'^(?P<name>.+)/a/diff/(?P<old_rev>\d+)/$', actions.do_diff),
    url(r'^(?P<name>.+)/a/diff/$', actions.do_diff),
    url(r'^(?P<name>.+)/a/discussion/$', actions.do_manage_discussion),
    url(r'^(?P<name>.+)/a/edit/$', actions.do_edit),
    url(r'^(?P<name>.+)/a/edit/revision/(?P<rev>\d+)/$', actions.do_edit),
    url(r'^(?P<name>.+)/a/export/(?P<format>(raw|html))/$', actions.do_export),
    url(r'^(?P<name>.+)/a/export/(?P<format>(raw|html))/(?P<rev>\d+)/$', actions.do_export),
    url(r'^(?P<name>.+)/a/export/meta/$', actions.do_metaexport),
    url(r'^(?P<name>.+)/a/log/(?P<pagination_page>\d+)/$', actions.do_log),
    url(r'^(?P<name>.+)/a/log/$', actions.do_log),
    url(r'^(?P<name>.+)/a/mv_back/$', actions.do_mv_back),
    url(r'^(?P<name>.+)/a/mv_baustelle/$', actions.do_mv_baustelle),
    url(r'^(?P<name>.+)/a/mv_discontinued/$', actions.do_mv_discontinued),
    url(r'^(?P<name>.+)/a/rename/$', actions.do_rename),
    url(r'^(?P<name>.+)/a/rename/force/$', actions.do_rename, {'force': True}),
    url(r'^(?P<name>.+)/a/revert/(?P<rev>\d+)/$', actions.do_revert),
    url(r'^(?P<name>.+)/a/revision/(?P<rev>\d+)/$', actions.do_show),
    url(r'^(?P<name>.+)/a/revision/(?P<rev>\d+)/no_redirect/$', actions.do_show, {'allow_redirect': False}),
    url(r'^(?P<name>.+)/a/subscribe/$', actions.do_subscribe),
    url(r'^(?P<name>.+)/a/udiff/(?P<old_rev>\d+)/(?P<new_rev>\d+)/$', actions.do_diff, {'udiff': True}),
    url(r'^(?P<name>.+)/a/udiff/(?P<old_rev>\d+)/$', actions.do_diff, {'udiff': True}),
    url(r'^(?P<name>.+)/a/udiff/$', actions.do_diff, {'udiff': True}),
    url(r'^(?P<name>.+)/a/unsubscribe/$', actions.do_unsubscribe),
    url(r'^(?P<name>.+)/no_redirect/$', actions.do_show, {'allow_redirect': False}),
    url(r'^(?P<name>.+)/$', actions.do_show),
])

handler404 = global_not_found
handler500 = server_error
