# -*- coding: utf-8 -*-
"""
    inyoka.ikhaya.urls
    ~~~~~~~~~~~~~~~~~~

    URL list for ikhaya.

    :copyright: (c) 2007-2021 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.conf import settings
from django.conf.urls import include, url

from . import views
from ..utils.http import global_not_found, server_error

urlpatterns = [
    url(r'^$', views.index),
    url(r'^full/$', views.index, {'full': True}),
    url(r'^(?P<page>\d+)/$', views.index),
    url(r'^full/(?P<page>\d+)/$', views.index, {'full': True}),
    url(r'^(?P<year>\d+)/(?P<month>\d+)/$', views.index),
    url(r'^(?P<year>\d+)/(?P<month>\d+)/full/$', views.index, {'full': True}),
    url(r'^(?P<year>\d+)/(?P<month>\d+)/(?P<page>\d+)/$', views.index),
    url(r'^(?P<year>\d+)/(?P<month>\d+)/full/(?P<page>\d+)/$', views.index, {'full': True}),
    url(r'^category/new/$', views.category_edit),
    url(r'^category/(?P<category_slug>[^/]+)/$', views.index),
    url(r'^category/(?P<category_slug>[^/]+)/full/$', views.index, {'full': True}),
    url(r'^category/(?P<category_slug>[^/]+)/(?P<page>\d+)/$', views.index),
    url(r'^category/(?P<category_slug>[^/]+)/full/(?P<page>\d+)/$', views.index, {'full': True}),
    url(r'^category/(?P<category_slug>[^/]+)/edit/$', views.category_edit),

    #: article related urls
    url(r'^(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/(?P<slug>[^/]+)/$', views.detail),
    url(r'^(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/(?P<slug>[^/]+)/delete/$',
        views.article_delete),
    url(r'^(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/(?P<slug>[^/]+)/edit/$',
        views.article_edit),
    url(r'^(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/(?P<slug>[^/]+)/subscribe/$',
        views.article_subscribe),
    url(r'^(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/(?P<slug>[^/]+)/unsubscribe/$',
        views.article_unsubscribe),
    url(r'^(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/(?P<slug>[^/]+)/reports/$',
        views.reports),
    url(r'^(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/(?P<slug>[^/]+)/new_report/$',
        views.report_new),
    url(r'^article/new/$', views.article_edit),
    url(r'^article/new/(?P<suggestion_id>\d+)/$', views.article_edit),

    #: comment related urls
    url(r'^comment/(?P<comment_id>\d+)/edit/$', views.comment_edit),
    url(r'^comment/(?P<comment_id>\d+)/hide/$', views.comment_hide),
    url(r'^comment/(?P<comment_id>\d+)/restore/$', views.comment_restore),

    #: report related urls
    url(r'^report/(?P<report_id>\d+)/hide/$', views.report_hide),
    url(r'^report/(?P<report_id>\d+)/restore/$', views.report_restore),
    url(r'^report/(?P<report_id>\d+)/solve/$', views.report_solve),
    url(r'^report/(?P<report_id>\d+)/unsolve/$', views.report_unsolve),
    url(r'^report/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/(?P<slug>[^/]+)/new/$',
        views.report_new),
    url(r'^reports/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/(?P<slug>[^/]+)/$',
        views.reports),
    url(r'^reports/$', views.reportlist),

    url(r'^archive/$', views.archive),

    url(r'^suggest/(?P<suggestion>\d+)/assign/(?P<username>[^/]+)/$', views.suggest_assign_to),
    url(r'^suggest/(?P<suggestion>\d+)/delete/$', views.suggest_delete),
    url(r'^suggest/new/$', views.suggest_edit),
    url(r'^suggestions/$', views.suggestions),
    url(r'^suggestions/subscribe/$', views.suggestions_subscribe),
    url(r'^suggestions/unsubscribe/$', views.suggestions_unsubscribe),

    url(r'^feeds/comments/(?P<mode>\w+)/(?P<count>\d+)/$', views.feed_comment, {'id': None}),
    url(r'^feeds/comments/(?P<id>\d+)/(?P<mode>\w+)/(?P<count>\d+)/$', views.feed_comment),
    url(r'^feeds/(?P<mode>\w+)/(?P<count>\d+)/$', views.feed_article, {'slug': None}),
    url(r'^feeds/(?P<slug>[^/]+)/(?P<mode>\w+)/(?P<count>\d+)/$', views.feed_article),

    url(r'^events/$', views.events),
    url(r'^events/all/$', views.events, {'show_all': True}),
    url(r'^events/invisible/$', views.events, {'invisible': True}),
    url(r'^event/suggest/$', views.event_suggest),
    url(r'^event/new/$', views.event_edit),
    url(r'^event/(?P<pk>\d+)/delete/$', views.event_delete),
    url(r'^event/(?P<pk>\d+)/edit/$', views.event_edit),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns.append(
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )

handler404 = global_not_found
handler500 = server_error
