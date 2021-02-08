# -*- coding: utf-8 -*-
"""
    inyoka.forum.urls
    ~~~~~~~~~~~~~~~~~

    URL list for the forum.

    :copyright: (c) 2007-2021 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.conf import settings
from django.conf.urls import include, url

from . import views
from ..utils.http import global_not_found, server_error

urlpatterns = [
    url(r'^$', views.index),
    url(r'^topic/(?P<topic_slug>[^/]+)/$', views.viewtopic),
    url(r'^topic/(?P<topic_slug>[^/]+)/(?P<page>\d+|last)/$', views.viewtopic),
    url(r'^topic/(?P<topic_slug>[^/]+)/reply/$', views.edit),
    url(r'^topic/(?P<topic_slug>[^/]+)/first_unread/$', views.first_unread_post),
    url(r'^topic/(?P<topic_slug>[^/]+)/last_post/$', views.last_post),
    url(r'^topic/(?P<topic_slug>[^/]+)/(?P<action>delete|hide)/$', views.delete_topic),
    url(r'^topic/(?P<topic_slug>[^/]+)/restore/$', views.restore_topic),
    url(r'^topic/(?P<topic_slug>[^/]+)/split/$', views.splittopic),
    url(r'^topic/(?P<topic_slug>[^/]+)/split/(?P<page>\d+)/$', views.splittopic),
    url(r'^topic/(?P<topic_slug>[^/]+)/move/$', views.movetopic),
    url(r'^topic/(?P<topic_slug>[^/]+)/(?P<page>\d+/)?solve/$', views.solve_topic, {'solved': True}),
    url(r'^topic/(?P<topic_slug>[^/]+)/(?P<page>\d+/)?unsolve/$', views.solve_topic, {'solved': False}),
    url(r'^topic/(?P<topic_slug>[^/]+)/(?P<page>\d+/)?lock/$', views.lock_topic, {'locked': True}),
    url(r'^topic/(?P<topic_slug>[^/]+)/(?P<page>\d+/)?unlock/$', views.lock_topic, {'locked': False}),
    url(r'^topic/(?P<topic_slug>[^/]+)/(?P<page>\d+/)?report/$', views.report),
    url(r'^topic/(?P<topic_slug>[^/]+)/subscribe', views.subscribe_topic),
    url(r'^topic/(?P<topic_slug>[^/]+)/unsubscribe', views.unsubscribe_topic),
    url(r'^topic/(?P<topic_slug>[^/]+)/next/$', views.next_topic),
    url(r'^topic/(?P<topic_slug>[^/]+)/previous/$', views.previous_topic),
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
    url(r'^newposts/$', views.topiclist, {'action': 'newposts'}),
    url(r'^newposts/(?P<page>\d+)/$', views.topiclist, {'action': 'newposts'}),
    url(r'^newposts/(?P<forum>[^/]+)/$', views.topiclist, {'action': 'newposts'}),
    url(r'^newposts/(?P<forum>[^/]+)/(?P<page>\d+)/$', views.topiclist, {'action': 'newposts'}),

    url(r'^last(?P<hours>\d+)/$', views.topiclist, {'action': 'last'}),
    url(r'^last(?P<hours>\d+)/(?P<page>\d+)/$', views.topiclist, {'action': 'last'}),
    url(r'^last(?P<hours>\d+)/(?P<forum>[^/]+)/$', views.topiclist, {'action': 'last'}),
    url(r'^last(?P<hours>\d+)/(?P<forum>[^/]+)/(?P<page>\d+)/$', views.topiclist, {'action': 'last'}),

    url(r'^unanswered/$', views.topiclist, {'action': 'unanswered'}),
    url(r'^unanswered/(?P<page>\d+)/$', views.topiclist, {'action': 'unanswered'}),
    url(r'^unanswered/(?P<forum>[^/]+)/$', views.topiclist, {'action': 'unanswered'}),
    url(r'^unanswered/(?P<forum>[^/]+)/(?P<page>\d+)/$', views.topiclist, {'action': 'unanswered'}),

    url(r'^unsolved/$', views.topiclist, {'action': 'unsolved'}),
    url(r'^unsolved/(?P<page>\d+)/$', views.topiclist, {'action': 'unsolved'}),
    url(r'^unsolved/(?P<forum>[^/]+)/$', views.topiclist, {'action': 'unsolved'}),
    url(r'^unsolved/(?P<forum>[^/]+)/(?P<page>\d+)/$', views.topiclist, {'action': 'unsolved'}),

    url(r'^egosearch/$', views.topiclist, {'action': 'author'}),
    url(r'^egosearch/(?P<page>\d+)/$', views.topiclist, {'action': 'author'}),
    url(r'^egosearch/(?P<forum>[^/]+)/$', views.topiclist, {'action': 'author'}),
    url(r'^egosearch/(?P<forum>[^/]+)/(?P<page>\d+)/$', views.topiclist, {'action': 'author'}),

    url(r'^author/(?P<user>[^/]+)/$', views.postlist),
    url(r'^author/(?P<user>[^/]+)/(?P<page>\d+)/$', views.postlist),
    url(r'^author/(?P<user>[^/]+)/topic/(?P<topic_slug>[^/]+)/$', views.postlist),
    url(r'^author/(?P<user>[^/]+)/topic/(?P<topic_slug>[^/]+)/(?P<page>\d+)/$', views.postlist),
    url(r'^author/(?P<user>[^/]+)/forum/(?P<forum_slug>[^/]+)/$', views.postlist),
    url(r'^author/(?P<user>[^/]+)/forum/(?P<forum_slug>[^/]+)/(?P<page>\d+)/$', views.postlist),

    url(r'^topic_author/(?P<user>[^/]+)/$', views.topiclist, {'action': 'topic_author'}),
    url(r'^topic_author/(?P<user>[^/]+)/(?P<page>\d+)/$', views.topiclist, {'action': 'topic_author'}),
    url(r'^topic_author/(?P<user>[^/]+)/(?P<forum>[^/]+)/$', views.topiclist, {'action': 'topic_author'}),
    url(r'^topic_author/(?P<user>[^/]+)/(?P<forum>[^/]+)/(?P<page>\d+)/$', views.topiclist, {'action': 'topic_author'}),

    url(r'^category/(?P<slug>[^/]+)/welcome/$', views.WelcomeMessageView.as_view()),
    url(r'^forum/(?P<slug>[^/]+)/welcome/$', views.WelcomeMessageView.as_view()),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns.append(
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )

handler404 = global_not_found
handler500 = server_error
