# -*- coding: utf-8 -*-
"""
    inyoka.forum.urls
    ~~~~~~~~~~~~~~~~~

    URL list for the forum.

    :copyright: (c) 2007-2016 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.conf import settings
from django.conf.urls import include, url

from . import views

urlpatterns = [
    url(r'^$', views.index),
    url(r'^topic/(?P<topic_slug>[^/]+)/$', views.viewtopic),
    url(r'^topic/(?P<topic_slug>[^/]+)/(?P<page>\d+)/$', views.viewtopic),
    url(r'^topic/(?P<topic_slug>[^/]+)/reply/$', views.edit),
    url(r'^topic/(?P<topic_slug>[^/]+)/first_unread/$', views.first_unread_post),
    url(r'^topic/(?P<topic_slug>[^/]+)/last_post/$', views.last_post),
    url(r'^topic/(?P<topic_slug>[^/]+)/(?P<action>delete|hide)/$', views.delete_topic),
    url(r'^topic/(?P<topic_slug>[^/]+)/restore/$', views.restore_topic),
    url(r'^topic/(?P<topic_slug>[^/]+)/split/$', views.splittopic),
    url(r'^topic/(?P<topic_slug>[^/]+)/split/(?P<page>\d+)/$', views.splittopic),
    url(r'^topic/(?P<topic_slug>[^/]+)/move/$', views.movetopic),
    url(r'^topic/(?P<topic_slug>[^/]+)/solve/$', views.change_status, {'solved': True}),
    url(r'^topic/(?P<topic_slug>[^/]+)/unsolve/$', views.change_status, {'solved': False}),
    url(r'^topic/(?P<topic_slug>[^/]+)/lock/$', views.change_lock_status, {'locked': True}),
    url(r'^topic/(?P<topic_slug>[^/]+)/unlock/$', views.change_lock_status, {'locked': False}),
    url(r'^topic/(?P<topic_slug>[^/]+)/report/$', views.report),
    url(r'^topic/(?P<topic_slug>[^/]+)/report_done/$', views.report, {'status': 'done'}),
    url(r'^topic/(?P<topic_slug>[^/]+)/subscribe', views.subscribe_topic),
    url(r'^topic/(?P<topic_slug>[^/]+)/unsubscribe', views.unsubscribe_topic),
    url(r'^topic/(?P<slug>[^/]+)/next/$', views.NextTopicView.as_view()),
    url(r'^topic/(?P<slug>[^/]+)/previous/$', views.NextTopicView.as_view(direction='older')),
    url(r'^reported_topics/$', views.reportlist),
    url(r'^reported_topics/(?P<mode>(un)?subscribe)/$', views.reported_topics_subscription),
    url(r'^post/(?P<post_id>\d+)/$', views.post),
    url(r'^post/(?P<post_id>\d+)/edit/$', views.edit),
    url(r'^post/(?P<quote_id>\d+)/quote/$', views.edit),
    url(r'^post/(?P<post_id>\d+)/restore/$', views.restore_post),
    url(r'^post/(?P<post_id>\d+)/(?P<action>delete|hide)/$', views.delete_post),
    url(r'^post/(?P<post_id>\d+)/(?P<action>ham|spam)/$', views.mark_ham_spam),
    url(r'^post/(?P<post_id>\d+)/revisions/$', views.revisions),
    url(r'^revision/(?P<rev_id>\d+)/restore/$', views.restore_revision),
    url(r'^forum/new/$', views.ForumCreateView.as_view()),
    url(r'^forum/(?P<slug>[^/]+)/$', views.forum),
    url(r'^forum/(?P<slug>[^/]+)/edit/$', views.ForumUpdateView.as_view()),
    url(r'^forum/(?P<slug>[^/]+)/subscribe/$', views.subscribe_forum),
    url(r'^forum/(?P<slug>[^/]+)/unsubscribe/$', views.unsubscribe_forum),
    url(r'^forum/(?P<slug>[^/]+)/(?P<page>\d+)/$', views.forum),
    url(r'^forum/(?P<forum_slug>[^/]+)/newtopic/$', views.edit),
    url(r'^feeds/(?P<mode>[a-z]+)/(?P<count>\d+)/$', views.forum_feed, {'slug': None}),
    url(r'^feeds/forum/(?P<slug>[^/]+)/(?P<mode>[a-z]+)/(?P<count>\d+)/$', views.forum_feed),
    url(r'^feeds/topic/(?P<slug>[^/]+)/(?P<mode>[a-z]+)/(?P<count>\d+)/$', views.topic_feed),
    url(r'^category/(?P<category>[^/]+)/$', views.index),
    url(r'^new_discussion/(?P<page_name>.+)/$', views.edit),
    url(r'^markread/$', views.markread),
    url(r'^category/(?P<slug>[^/]+)/markread/$', views.markread),
    url(r'^forum/(?P<slug>[^/]+)/markread/$', views.markread),

    # special searches
    url(
        r'^unanswered/$',
        views.UnansweredTopicsListView.as_view(),
        name='forum_list_unanswered_topics',
    ),
    url(
        r'^unanswered/(?P<page>\d+)/$',
        views.UnansweredTopicsListView.as_view(),
        name='forum_list_unanswered_topics',
    ),
    url(
        r'^unanswered/(?P<slug>[^/]+)/$',
        views.UnansweredTopicsListView.as_view(),
        name='forum_list_unanswered_topics',
    ),
    url(
        r'^unanswered/(?P<slug>[^/]+)/(?P<page>\d+)/$',
        views.UnansweredTopicsListView.as_view(),
        name='forum_list_unanswered_topics',
    ),

    url(
        r'^unsolved/$',
        views.UnsolvedTopicsListView.as_view(),
        name='forum_list_unsolved_topics',
    ),
    url(
        r'^unsolved/(?P<page>\d+)/$',
        views.UnsolvedTopicsListView.as_view(),
        name='forum_list_unsolved_topics',
    ),
    url(
        r'^unsolved/(?P<slug>[^/]+)/$',
        views.UnsolvedTopicsListView.as_view(),
        name='forum_list_unsolved_topics',
    ),
    url(
        r'^unsolved/(?P<slug>[^/]+)/(?P<page>\d+)/$',
        views.UnsolvedTopicsListView.as_view(),
        name='forum_list_unsolved_topics',
    ),
    url(
        r'^author/(?P<username>[^/]+)/$',
        views.AuthorPostListView.as_view(),
        name='forum_author_post_list',
    ),
    url(
        r'^author/(?P<username>[^/]+)/(?P<page>\d+)/$',
        views.AuthorPostListView.as_view(),
        name='forum_author_post_list',
    ),
    url(
        r'^author/(?P<username>[^/]+)/topic/(?P<slug>[^/]+)/$',
        views.AuthorPostListView.as_view(),
        name='forum_author_post_topic_list',
    ),
    url(
        r'^author/(?P<username>[^/]+)/topic/(?P<slug>[^/]+)/(?P<page>\d+)/$',
        views.AuthorPostListView.as_view(),
        name='forum_author_post_topic_list',
    ),
    url(
        r'^author/(?P<username>[^/]+)/forum/(?P<slug>[^/]+)/$',
        views.AuthorPostForumListView.as_view(),
        name='forum_author_post_forum_list',
    ),
    url(
        r'^author/(?P<username>[^/]+)/forum/(?P<slug>[^/]+)/(?P<page>\d+)/$',
        views.AuthorPostListView.as_view(),
        name='forum_author_post_forum_list',
    ),
    url(
        r'^topic_author/(?P<username>[^/]+)/$',
        views.AuthorTopicListView.as_view(),
        name='forum_author_topic_list',
    ),
    url(
        r'^topic_author/(?P<username>[^/]+)/(?P<page>\d+)/$',
        views.AuthorTopicListView.as_view(),
        name='forum_author_topic_list',
    ),
    url(
        r'^topic_author/(?P<username>[^/]+)/(?P<slug>[^/]+)/$',
        views.AuthorTopicListView.as_view(),
        name='forum_author_topic_list',
    ),
    url(
        r'^topic_author/(?P<username>[^/]+)/(?P<slug>[^/]+)/(?P<page>\d+)/$',
        views.AuthorTopicListView.as_view(),
        name='forum_author_topic_list',
    ),
    url(
        r'^egosearch/$',
        views.EgosearchView.as_view(),
        name='forum_egosearch',
    ),
    url(
        r'^egosearch/(?P<page>\d+)/$',
        views.EgosearchView.as_view(),
        name='forum_egosearch',
    ),
    url(
        r'^egosearch/(?P<slug>[^/]+)/$',
        views.EgosearchView.as_view(),
        name='forum_egosearch',
    ),
    url(
        r'^egosearch/(?P<slug>[^/]+)/(?P<page>\d+)/$',
        views.EgosearchView.as_view(),
        name='forum_egosearch',
    ),
    url(
        r'^last(?P<hours>\d+)/$',
        views.LastTopicsListView.as_view(),
        name='forum_last_topics',
    ),
    url(
        r'^last(?P<hours>\d+)/(?P<page>\d+)/$',
        views.LastTopicsListView.as_view(),
        name='forum_last_topics',
    ),
    url(
        r'^last(?P<hours>\d+)/(?P<slug>[^/]+)/$',
        views.LastTopicsListView.as_view(),
        name='forum_last_topics',
    ),
    url(
        r'^last(?P<hours>\d+)/(?P<slug>[^/]+)/(?P<page>\d+)/$',
        views.LastTopicsListView.as_view(),
        name='forum_last_topics',
    ),
    url(
        r'^newposts/$',
        views.UnreadTopicsListView.as_view(),
        name='forum_unread_topic_list',
    ),
    url(
        r'^newposts/(?P<page>\d+)/$',
        views.UnreadTopicsListView.as_view(),
        name='forum_unread_topic_list',
    ),
    url(
        r'^newposts/(?P<slug>[^/]+)/$',
        views.UnreadTopicsListView.as_view(),
        name='forum_unread_topic_list',
    ),
    url(
        r'^newposts/(?P<slug>[^/]+)/(?P<page>\d+)/$',
        views.UnreadTopicsListView.as_view(),
        name='forum_unread_topic_list',
    ),

    url(r'^category/(?P<slug>[^/]+)/welcome/$', views.WelcomeMessageView.as_view()),
    url(r'^forum/(?P<slug>[^/]+)/welcome/$', views.WelcomeMessageView.as_view()),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns.append(
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )

handler404 = 'inyoka.utils.http.global_not_found'
