# -*- coding: utf-8 -*-
"""
    inyoka.ikhaya.urls
    ~~~~~~~~~~~~~~~~~~

    URL list for ikhaya.

    :copyright: (c) 2007-2012 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from django.conf.urls.defaults import patterns


urlpatterns = patterns('inyoka.ikhaya.views',
    (r'^$', 'index'),
    (r'^full/$', 'index', {'full': True}),
    (r'^(?P<page>\d+)/$', 'index'),
    (r'^(?P<page>\d+)/full/$', 'index', {'full': True}),
    (r'^(?P<year>\d+)/(?P<month>\d+)/$', 'index'),
    (r'^(?P<year>\d+)/(?P<month>\d+)/full/$', 'index', {'full': True}),
    (r'^(?P<year>\d+)/(?P<month>\d+)/(?P<page>\d+)/$', 'index'),
    (r'^(?P<year>\d+)/(?P<month>\d+)/(?P<page>\d+)/full/$', 'index', {'full': True}),
    (r'^category/new/$', 'category_edit'),
    (r'^category/(?P<category_slug>[^/]+)/$', 'index'),
    (r'^category/(?P<category_slug>[^/]+)/full/$', 'index', {'full': True}),
    (r'^category/(?P<category_slug>[^/]+)/(?P<page>\d+)/$', 'index'),
    (r'^category/(?P<category_slug>[^/]+)/(?P<page>\d+)/full/$', 'index', {'full': True}),
    (r'^category/(?P<category_slug>[^/]+)/edit/$', 'category_edit'),

    #: article related urls
    (r'^(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/(?P<slug>[^/]+)/$', 'detail'),
    (r'^(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/(?P<slug>[^/]+)/delete/$',
        'article_delete'),
    (r'^(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/(?P<slug>[^/]+)/edit/$',
        'article_edit'),
    (r'^(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/(?P<slug>[^/]+)/subscribe/$',
        'article_subscribe'),
    (r'^(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/(?P<slug>[^/]+)/unsubscribe/$',
        'article_unsubscribe'),
    (r'^(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/(?P<slug>[^/]+)/reports/$',
        'reports'),
    (r'^(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/(?P<slug>[^/]+)/new_report/$',
        'report_new'),
    (r'^article/new/$', 'article_edit'),
    (r'^article/new/(?P<suggestion_id>\d+)/$', 'article_edit'),

    #: comment related urls
    (r'^comment/(?P<comment_id>\d+)/edit/$', 'comment_edit'),
    (r'^comment/(?P<comment_id>\d+)/hide/$', 'comment_hide'),
    (r'^comment/(?P<comment_id>\d+)/restore/$', 'comment_restore'),

    #: report related urls
    (r'^report/(?P<report_id>\d+)/hide/$', 'report_hide'),
    (r'^report/(?P<report_id>\d+)/restore/$', 'report_restore'),
    (r'^report/(?P<report_id>\d+)/solve/$', 'report_solve'),
    (r'^report/(?P<report_id>\d+)/unsolve/$', 'report_unsolve'),
    (r'^report/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/(?P<slug>[^/]+)/new/$',
        'report_new'),
    (r'^reports/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/(?P<slug>[^/]+)/$',
        'reports'),
    (r'^reports/$', 'reportlist'),

    (r'^archive/$', 'archive'),

    (r'^suggest/(?P<suggestion>\d+)/assign/(?P<username>[^/]+)/$', 'suggest_assign_to'),
    (r'^suggest/(?P<suggestion>\d+)/delete/$', 'suggest_delete'),
    (r'^suggest/new/$', 'suggest_edit'),
    (r'^suggestions/$', 'suggestions'),
    (r'^suggestions/subscribe/$', 'suggestions_subscribe'),
    (r'^suggestions/unsubscribe/$', 'suggestions_unsubscribe'),

    (r'^feeds/comments/(?P<mode>\w+)/(?P<count>\d+)/$', 'feed_comment', {'id': None}),
    (r'^feeds/comments/(?P<id>\d+)/(?P<mode>\w+)/(?P<count>\d+)/$', 'feed_comment'),
    (r'^feeds/(?P<mode>\w+)/(?P<count>\d+)/$', 'feed_article', {'slug': None}),
    (r'^feeds/(?P<slug>[^/]+)/(?P<mode>\w+)/(?P<count>\d+)/$', 'feed_article'),

    (r'^events/$', 'events'),
    (r'^events/all/$', 'events', {'show_all': True}),
    (r'^events/invisible/$', 'events', {'invisible':True}),
    #(r'^events/suggestions/$', 'events_suggestions'),
    (r'^event/suggest/$', 'event_suggest'),
    (r'^event/new/$', 'event_edit'),
    (r'^event/(?P<pk>\d+)/delete/$', 'event_delete'),
    (r'^event/(?P<pk>\d+)/edit/$', 'event_edit'),
)


handler404 = 'inyoka.utils.urls.global_not_found'
