# -*- coding: utf-8 -*-
"""
    inyoka.forum.urls
    ~~~~~~~~~~~~~~~~~

    URL list for the forum.

    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from django.conf.urls.defaults import patterns


urlpatterns = patterns('inyoka.forum.views',
    (r'^$', 'index'),
    (r'^topic/(?P<topic_slug>[^/]+)/$', 'viewtopic'),
    (r'^topic/(?P<topic_slug>[^/]+)/(?P<page>\d+)/$', 'viewtopic'),
    (r'^topic/(?P<topic_slug>[^/]+)/reply/$', 'edit'),
    (r'^topic/(?P<topic_slug>[^/]+)/first_unread/$', 'first_unread_post'),
    (r'^topic/(?P<topic_slug>[^/]+)/(?P<action>delete|hide)/$', 'delete_topic'),
    (r'^topic/(?P<topic_slug>[^/]+)/restore/$', 'restore_topic'),
    (r'^topic/(?P<topic_slug>[^/]+)/split/$', 'splittopic'),
    (r'^topic/(?P<topic_slug>[^/]+)/split/(?P<page>\d+)/$', 'splittopic'),
    (r'^topic/(?P<topic_slug>[^/]+)/move/$', 'movetopic'),
    (r'^topic/(?P<topic_slug>[^/]+)/solve/$', 'change_status',
                                    {'solved': True}),
    (r'^topic/(?P<topic_slug>[^/]+)/unsolve/$', 'change_status',
                                    {'solved': False}),
    (r'^topic/(?P<topic_slug>[^/]+)/lock/$', 'change_lock_status',
                                    {'locked': True}),
    (r'^topic/(?P<topic_slug>[^/]+)/unlock/$', 'change_lock_status',
                                    {'locked': False}),
    (r'^topic/(?P<topic_slug>[^/]+)/report/$', 'report'),
    (r'^topic/(?P<topic_slug>[^/]+)/report_done/$', 'report',
                                    {'status': 'done'}),
    (r'^topic/(?P<topic_slug>[^/]+)/subscribe', 'subscribe_topic'),
    (r'^topic/(?P<topic_slug>[^/]+)/unsubscribe', 'unsubscribe_topic'),
    (r'^topic/(?P<topic_slug>[^/]+)/next/$', 'next_topic'),
    (r'^topic/(?P<topic_slug>[^/]+)/previous/$', 'previous_topic'),
    (r'^reported_topics/$', 'reportlist'),
    (r'^reported_topics/(?P<mode>(un)?subscribe)/$', 'reported_topics_subscription'),
    (r'^post/(?P<post_id>\d+)/$', 'post'),
    (r'^post/(?P<post_id>\d+)/edit/$', 'edit'),
    (r'^post/(?P<quote_id>\d+)/quote/$', 'edit'),
    (r'^post/(?P<post_id>\d+)/restore/$', 'restore_post'),
    (r'^post/(?P<post_id>\d+)/(?P<action>delete|hide)/$', 'delete_post'),
    (r'^post/(?P<post_id>\d+)/revisions/$', 'revisions'),
    (r'^revision/(?P<rev_id>\d+)/restore/$', 'restore_revision'),
    (r'^forum/new/$', 'forum_edit'),
    (r'^forum/new/(?P<parent>[^/]+)/$', 'forum_edit'),
    (r'^forum/(?P<slug>[^/]+)/$', 'forum'),
    (r'^forum/(?P<slug>[^/]+)/edit/$', 'forum_edit'),
    (r'^forum/(?P<slug>[^/]+)/subscribe/$', 'subscribe_forum'),
    (r'^forum/(?P<slug>[^/]+)/unsubscribe/$', 'unsubscribe_forum'),
    (r'^forum/(?P<slug>[^/]+)/(?P<page>\d+)/$', 'forum'),
    (r'^forum/(?P<forum_slug>[^/]+)/newtopic/$', 'edit'),
    (r'^feeds/(?P<mode>[a-z]+)/(?P<count>\d+)/$', 'forum_feed', {'slug': None}),
    (r'^feeds/forum/(?P<slug>[^/]+)/(?P<mode>[a-z]+)/(?P<count>\d+)/$', 'forum_feed'),
    (r'^feeds/topic/(?P<slug>[^/]+)/(?P<mode>[a-z]+)/(?P<count>\d+)/$', 'topic_feed'),
    (r'^category/(?P<category>[^/]+)/$', 'index'),
    (r'^new_discussion/(?P<page_name>.+)/$', 'edit'),
    (r'^markread/$', 'markread'),
    (r'^category/(?P<slug>[^/]+)/markread/$', 'markread'),
    (r'^forum/(?P<slug>[^/]+)/markread/$', 'markread'),
    # special searches
    (r'^newposts/$', 'topiclist', {'action': 'newposts'}),
    (r'^newposts/(?P<page>\d+)/$', 'topiclist', {'action': 'newposts'}),
    (r'^newposts/(?P<forum>[^/]+)/$', 'topiclist', {'action': 'newposts'}),
    (r'^newposts/(?P<forum>[^/]+)/(?P<page>\d+)/$', 'topiclist', {'action': 'newposts'}),

    (r'^last(?P<hours>\d+)/$', 'topiclist', {'action': 'last'}),
    (r'^last(?P<hours>\d+)/(?P<page>\d+)/$', 'topiclist', {'action': 'last'}),
    (r'^last(?P<hours>\d+)/(?P<forum>[^/]+)/$', 'topiclist', {'action': 'last'}),
    (r'^last(?P<hours>\d+)/(?P<forum>[^/]+)/(?P<page>\d+)/$', 'topiclist', {'action': 'last'}),

    (r'^unanswered/$', 'topiclist', {'action': 'unanswered'}),
    (r'^unanswered/(?P<page>\d+)/$', 'topiclist', {'action': 'unanswered'}),
    (r'^unanswered/(?P<forum>[^/]+)/$', 'topiclist', {'action': 'unanswered'}),
    (r'^unanswered/(?P<forum>[^/]+)/(?P<page>\d+)/$', 'topiclist', {'action': 'unanswered'}),

    (r'^unsolved/$', 'topiclist', {'action': 'unsolved'}),
    (r'^unsolved/(?P<page>\d+)/$', 'topiclist', {'action': 'unsolved'}),
    (r'^unsolved/(?P<forum>[^/]+)/$', 'topiclist', {'action': 'unsolved'}),
    (r'^unsolved/(?P<forum>[^/]+)/(?P<page>\d+)/$', 'topiclist', {'action': 'unsolved'}),

    (r'^egosearch/$', 'topiclist', {'action': 'author'}),
    (r'^egosearch/(?P<page>\d+)/$', 'topiclist', {'action': 'author'}),
    (r'^egosearch/(?P<forum>[^/]+)/$', 'topiclist', {'action': 'author'}),
    (r'^egosearch/(?P<forum>[^/]+)/(?P<page>\d+)/$', 'topiclist', {'action': 'author'}),

    (r'^author/(?P<user>[^/]+)/$', 'topiclist', {'action': 'author'}),
    (r'^author/(?P<user>[^/]+)/(?P<page>\d+)/$', 'topiclist', {'action': 'author'}),
    (r'^author/(?P<user>[^/]+)/(?P<forum>[^/]+)/$', 'topiclist', {'action': 'author'}),
    (r'^author/(?P<user>[^/]+)/(?P<forum>[^/]+)/(?P<page>\d+)/$', 'topiclist', {'action': 'author'}),

    (r'^topic_author/(?P<user>[^/]+)/$', 'topiclist', {'action': 'topic_author'}),
    (r'^topic_author/(?P<user>[^/]+)/(?P<page>\d+)/$', 'topiclist', {'action': 'topic_author'}),
    (r'^topic_author/(?P<user>[^/]+)/(?P<forum>[^/]+)/$', 'topiclist', {'action': 'topic_author'}),
    (r'^topic_author/(?P<user>[^/]+)/(?P<forum>[^/]+)/(?P<page>\d+)/$', 'topiclist', {'action': 'topic_author'}),

    (r'^category/(?P<slug>[^/]+)/welcome/$', 'welcome'),
    (r'^forum/(?P<slug>[^/]+)/welcome/$', 'welcome'),
)


handler404 = 'inyoka.forum.views.not_found'
