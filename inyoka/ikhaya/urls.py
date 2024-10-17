"""
    inyoka.ikhaya.urls
    ~~~~~~~~~~~~~~~~~~

    URL list for ikhaya.

    :copyright: (c) 2007-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.conf import settings
from django.urls import include, path, re_path
from django.views.decorators.cache import cache_page

from ..utils.http import global_not_found, server_error, bad_request_view, \
    permission_denied_view
from . import views

urlpatterns = [
    path('', views.index),
    path('full/', views.index, {'full': True}),
    path('<int:page>/', views.index),
    path('full/<int:page>/', views.index, {'full': True}),
    path('<int:year>/<int:month>/', views.index),
    path('<int:year>/<int:month>/full/', views.index, {'full': True}),
    path('<int:year>/<int:month>/<int:page>/', views.index),
    path('<int:year>/<int:month>/full/<int:page>/', views.index, {'full': True}),
    path('category/new/', views.category_edit),
    path('category/<str:category_slug>/', views.index),
    path('category/<str:category_slug>/full/', views.index, {'full': True}),
    path('category/<str:category_slug>/<int:page>/', views.index),
    path('category/<str:category_slug>/full/<int:page>/', views.index, {'full': True}),
    path('category/<str:category_slug>/edit/', views.category_edit),

    #: article related urls
    path('<int:year>/<int:month>/<int:day>/<str:slug>/', views.detail),
    path('<int:year>/<int:month>/<int:day>/<str:slug>/delete/',
        views.article_delete),
    path('<int:year>/<int:month>/<int:day>/<str:slug>/edit/',
        views.article_edit),
    path('<int:year>/<int:month>/<int:day>/<str:slug>/subscribe/',
        views.article_subscribe),
    path('<int:year>/<int:month>/<int:day>/<str:slug>/unsubscribe/',
        views.article_unsubscribe),
    path('<int:year>/<int:month>/<int:day>/<str:slug>/reports/',
        views.reports),
    path('<int:year>/<int:month>/<int:day>/<str:slug>/new_report/',
        views.report_new),
    path('article/new/', views.article_edit),
    path('article/new/<int:suggestion_id>/', views.article_edit),

    #: comment related urls
    path('comment/<int:comment_id>/edit/', views.comment_edit),
    path('comment/<int:comment_id>/hide/', views.comment_hide),
    path('comment/<int:comment_id>/restore/', views.comment_restore),

    #: report related urls
    path('report/<int:report_id>/hide/', views.report_hide),
    path('report/<int:report_id>/restore/', views.report_restore),
    path('report/<int:report_id>/solve/', views.report_solve),
    path('report/<int:report_id>/unsolve/', views.report_unsolve),
    path('report/<int:year>/<int:month>/<int:day>/<str:slug>/new/',
        views.report_new),
    path('reports/<int:year>/<int:month>/<int:day>/<str:slug>/',
        views.reports),
    path('reports/', views.reportlist),

    path('archive/', views.archive),

    path('suggest/<int:suggestion>/assign/<str:username>/', views.suggest_assign_to),
    path('suggest/<int:suggestion>/delete/', views.suggest_delete),
    path('suggest/new/', views.suggest_edit),
    path('suggestions/', views.suggestions),
    path('suggestions/subscribe/', views.suggestions_subscribe),
    path('suggestions/unsubscribe/', views.suggestions_unsubscribe),

    re_path(r'^feeds/comments/(?P<mode>\w+)/(?P<count>\d+)/$',
            cache_page(60 * 5)(views.IkhayaCommentAtomFeed())),
    re_path(r'^feeds/comments/(?P<id>\d+)/(?P<mode>\w+)/(?P<count>\d+)/$',
            cache_page(60 * 5)(views.IkhayaArticleCommentAtomFeed())),
    re_path(r'^feeds/(?P<mode>\w+)/(?P<count>\d+)/$',
            cache_page(60 * 5)(views.IkhayaAtomFeed())),
    re_path(r'^feeds/(?P<slug>[^/]+)/(?P<mode>\w+)/(?P<count>\d+)/$',
            cache_page(60 * 5)(views.IkhayaCategoryAtomFeed())),

    path('events/', views.events),
    path('events/all/', views.events, {'show_all': True}),
    path('events/invisible/', views.events, {'invisible': True}),
    path('event/suggest/', views.event_suggest),
    path('event/new/', views.event_edit),
    path('event/<int:pk>/delete/', views.event_delete),
    path('event/<int:pk>/edit/', views.event_edit),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns.append(
        path('__debug__/', include(debug_toolbar.urls)),
    )

handler400 = bad_request_view
handler403 = permission_denied_view
handler404 = global_not_found
handler500 = server_error
