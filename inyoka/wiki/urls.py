"""
    inyoka.wiki.urls
    ~~~~~~~~~~~~~~~~

    URL list for the wiki.

    :copyright: (c) 2007-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.conf import settings
from django.urls import include, path, re_path
from django.views.decorators.cache import cache_page

from ..utils.http import global_not_found, server_error, bad_request_view, \
    permission_denied_view
from . import actions, views

urlpatterns = [
    path('', views.index),
    path('_image/', views.get_image_resource),
    path('_newpage/', views.redirect_new_page),
    path('_attachment/', views.get_attachment),

    path('_feed/<int:count>/', cache_page(60 * 5)(views.WikiAtomFeed())),
    path('<path:page_name>/a/feed/', cache_page(60 * 5)(views.WikiPageAtomFeed()), {'count': 10}),
    path('<path:page_name>/a/feed/<int:count>/', cache_page(60 * 5)(views.WikiPageAtomFeed())),

    path('wiki/recentchanges/', views.recentchanges),
    path('wiki/missingpages/', views.missingpages),
    path('wiki/randompages/', views.randompages),
    path('wiki/tagcloud/', views.show_tag_cloud),
    path('wiki/tags/', views.show_tag_list),
    path('wiki/tags/<path:tag>/', views.show_pages_by_tag)
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns.append(
        path('__debug__/', include(debug_toolbar.urls)),
    )

urlpatterns.extend([
    re_path(r'^wiki/create/?$', actions.do_create),
    path('wiki/create/<path:name>/', actions.do_create),
    path('<path:name>/a/attachments/', actions.do_attach),
    path('<path:name>/a/backlinks/', actions.do_backlinks),
    path('<path:name>/a/delete/', actions.do_delete),
    path('<path:name>/a/diff/<int:old_rev>/<int:new_rev>/', actions.do_diff),
    path('<path:name>/a/diff/<int:old_rev>/', actions.do_diff),
    path('<path:name>/a/diff/', actions.do_diff),
    path('<path:name>/a/discussion/', actions.do_manage_discussion),
    path('<path:name>/a/edit/', actions.do_edit),
    path('<path:name>/a/edit/revision/<int:rev>/', actions.do_edit),
    re_path(r'^(?P<name>.+)/a/export/(?P<format>(raw|html))/$', actions.do_export),
    re_path(r'^(?P<name>.+)/a/export/(?P<format>(raw|html))/(?P<rev>\d+)/$', actions.do_export),
    path('<path:name>/a/export/meta/', actions.do_metaexport),
    path('<path:name>/a/log/<int:pagination_page>/', actions.do_log),
    path('<path:name>/a/log/', actions.do_log),
    path('<path:name>/a/mv_back/', actions.do_mv_back),
    path('<path:name>/a/mv_baustelle/', actions.do_mv_baustelle),
    path('<path:name>/a/mv_discontinued/', actions.do_mv_discontinued),
    path('<path:name>/a/rename/', actions.do_rename),
    path('<path:name>/a/rename/force/', actions.do_rename, {'force': True}),
    path('<path:name>/a/revert/<int:rev>/', actions.do_revert),
    path('<path:name>/a/revision/<int:rev>/', actions.do_show),
    path('<path:name>/a/revision/<int:rev>/no_redirect/', actions.do_show, {'allow_redirect': False}),
    path('<path:name>/a/subscribe/', actions.do_subscribe),
    path('<path:name>/a/udiff/<int:old_rev>/<int:new_rev>/', actions.do_diff, {'udiff': True}),
    path('<path:name>/a/udiff/<int:old_rev>/', actions.do_diff, {'udiff': True}),
    path('<path:name>/a/udiff/', actions.do_diff, {'udiff': True}),
    path('<path:name>/a/unsubscribe/', actions.do_unsubscribe),
    path('<path:name>/no_redirect/', actions.do_show, {'allow_redirect': False}),
    path('<path:name>/', actions.do_show),
])

handler400 = bad_request_view
handler403 = permission_denied_view
handler404 = global_not_found
handler500 = server_error
