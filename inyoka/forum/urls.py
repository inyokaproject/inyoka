"""
    inyoka.forum.urls
    ~~~~~~~~~~~~~~~~~

    URL list for the forum.

    :copyright: (c) 2007-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.conf import settings
from django.urls import include, path, re_path
from django.views.decorators.cache import cache_page

from ..utils.http import (
    bad_request_view,
    global_not_found,
    permission_denied_view,
    server_error,
)
from . import views

urlpatterns = [
    path('', views.index),
    path('topic/<str:topic_slug>/', views.viewtopic),
    re_path(r'^topic/(?P<topic_slug>[^/]+)/(?P<page>\d+|last)/$', views.viewtopic),
    path('topic/<str:topic_slug>/reply/', views.edit),
    path('topic/<str:topic_slug>/first_unread/', views.first_unread_post),
    path('topic/<str:topic_slug>/last_post/', views.last_post),
    re_path(r'^topic/(?P<topic_slug>[^/]+)/(?P<action>delete|hide)/$', views.delete_topic),
    path('topic/<str:topic_slug>/restore/', views.restore_topic),
    path('topic/<str:topic_slug>/split/', views.splittopic),
    path('topic/<str:topic_slug>/split/<int:page>/', views.splittopic),
    path('topic/<str:topic_slug>/move/', views.movetopic),
    re_path(r'^topic/(?P<topic_slug>[^/]+)/(?P<page>\d+/)?solve/$', views.solve_topic, {'solved': True}),
    re_path(r'^topic/(?P<topic_slug>[^/]+)/(?P<page>\d+/)?unsolve/$', views.solve_topic, {'solved': False}),
    re_path(r'^topic/(?P<topic_slug>[^/]+)/(?P<page>\d+/)?lock/$', views.lock_topic, {'locked': True}),
    re_path(r'^topic/(?P<topic_slug>[^/]+)/(?P<page>\d+/)?unlock/$', views.lock_topic, {'locked': False}),
    re_path(r'^topic/(?P<topic_slug>[^/]+)/(?P<page>\d+/)?report/$', views.report),
    re_path(r'^topic/(?P<topic_slug>[^/]+)/subscribe', views.subscribe_topic),
    re_path(r'^topic/(?P<topic_slug>[^/]+)/unsubscribe', views.unsubscribe_topic),
    path('topic/<str:topic_slug>/next/', views.next_topic),
    path('topic/<str:topic_slug>/previous/', views.previous_topic),
    path('reported_topics/', views.reportlist),
    re_path(r'^reported_topics/(?P<mode>(un)?subscribe)/$', views.reported_topics_subscription),
    path('post/<int:post_id>/', views.post),
    path('post/<int:post_id>/edit/', views.edit),
    path('post/<int:quote_id>/quote/', views.edit),
    path('post/<int:post_id>/restore/', views.restore_post),
    re_path(r'^post/(?P<post_id>\d+)/(?P<action>delete|hide)/$', views.delete_post),
    re_path(r'^post/(?P<post_id>\d+)/(?P<action>ham|spam)/$', views.mark_ham_spam),
    path('post/<int:post_id>/revisions/', views.revisions),
    path('revision/<int:rev_id>/restore/', views.restore_revision),
    path('forum/new/', views.ForumCreateView.as_view()),
    path('forum/<str:slug>/', views.forum),
    path('forum/<str:slug>/edit/', views.ForumUpdateView.as_view()),
    path('forum/<str:slug>/subscribe/', views.subscribe_forum),
    path('forum/<str:slug>/unsubscribe/', views.unsubscribe_forum),
    path('forum/<str:slug>/<int:page>/', views.forum),
    path('forum/<str:forum_slug>/newtopic/', views.edit),

    re_path(r'^feeds/(?P<mode>[a-z]+)/(?P<count>\d+)/$', cache_page(60 * 5)(views.ForumAtomFeed())),
    re_path(r'^feeds/forum/(?P<slug>[^/]+)/(?P<mode>[a-z]+)/(?P<count>\d+)/$',
            cache_page(60 * 5)(views.OneForumAtomFeed())),
    re_path(r'^feeds/topic/(?P<slug>[^/]+)/(?P<mode>[a-z]+)/(?P<count>\d+)/$',
            cache_page(60 * 5)(views.ForumTopicAtomFeed())),

    path('category/<str:category>/', views.index),
    path('new_discussion/<path:page_name>/', views.edit),
    path('markread/', views.markread),
    path('category/<str:slug>/markread/', views.markread),
    path('forum/<str:slug>/markread/', views.markread),

    # special searches
    path('newposts/', views.topiclist, {'action': 'newposts'}),
    path('newposts/<int:page>/', views.topiclist, {'action': 'newposts'}),
    path('newposts/<str:forum>/', views.topiclist, {'action': 'newposts'}),
    path('newposts/<str:forum>/<int:page>/', views.topiclist, {'action': 'newposts'}),

    path('last<int:hours>/', views.topiclist, {'action': 'last'}),
    path('last<int:hours>/<int:page>/', views.topiclist, {'action': 'last'}),
    path('last<int:hours>/<str:forum>/', views.topiclist, {'action': 'last'}),
    path('last<int:hours>/<str:forum>/<int:page>/', views.topiclist, {'action': 'last'}),

    path('unanswered/', views.topiclist, {'action': 'unanswered'}),
    path('unanswered/<int:page>/', views.topiclist, {'action': 'unanswered'}),
    path('unanswered/<str:forum>/', views.topiclist, {'action': 'unanswered'}),
    path('unanswered/<str:forum>/<int:page>/', views.topiclist, {'action': 'unanswered'}),

    path('unsolved/', views.topiclist, {'action': 'unsolved'}),
    path('unsolved/<int:page>/', views.topiclist, {'action': 'unsolved'}),
    path('unsolved/<str:forum>/', views.topiclist, {'action': 'unsolved'}),
    path('unsolved/<str:forum>/<int:page>/', views.topiclist, {'action': 'unsolved'}),

    path('egosearch/', views.topiclist, {'action': 'author'}),
    path('egosearch/<int:page>/', views.topiclist, {'action': 'author'}),
    path('egosearch/<str:forum>/', views.topiclist, {'action': 'author'}),
    path('egosearch/<str:forum>/<int:page>/', views.topiclist, {'action': 'author'}),

    path('author/<str:user>/', views.postlist),
    path('author/<str:user>/<int:page>/', views.postlist),
    path('author/<str:user>/topic/<str:topic_slug>/', views.postlist),
    path('author/<str:user>/topic/<str:topic_slug>/<int:page>/', views.postlist),
    path('author/<str:user>/forum/<str:forum_slug>/', views.postlist),
    path('author/<str:user>/forum/<str:forum_slug>/<int:page>/', views.postlist),

    path('topic_author/<str:user>/', views.topiclist, {'action': 'topic_author'}),
    path('topic_author/<str:user>/<int:page>/', views.topiclist, {'action': 'topic_author'}),
    path('topic_author/<str:user>/<str:forum>/', views.topiclist, {'action': 'topic_author'}),
    path('topic_author/<str:user>/<str:forum>/<int:page>/', views.topiclist, {'action': 'topic_author'}),

    path('category/<str:slug>/welcome/', views.WelcomeMessageView.as_view()),
    path('forum/<str:slug>/welcome/', views.WelcomeMessageView.as_view()),
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
