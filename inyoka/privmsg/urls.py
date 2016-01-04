# -*- coding: utf-8 -*-
"""
    inyoka.privmsg.urls
    ~~~~~~~~~~~~~~~~~~~

    The urls for the main portal (index page, error pages, login page etc.)

    :copyright: (c) 2007-2016 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.conf import settings
from django.conf.urls import include, url

from . import views

urlpatterns = [
    # folder views
    url(r'^inbox/$', views.InboxedMessagesView.as_view(),
        name='privmsg-inbox',),
    url(r'^inbox/(?P<page>\d+)/$', views.InboxedMessagesView.as_view(),
        name='privmsg-inbox-page'),
    url(r'^inbox/all/$', views.InboxedMessagesView.as_view(), {'one_page': True},
        name='privmsg-inbox-all'),
    url(r'^archive/$', views.ArchivedMessagesView.as_view(),
        name='privmsg-archive'),
    url(r'^archive/(?P<page>\d+)/$', views.ArchivedMessagesView.as_view(),
        name='privmsg-archive-page'),
    url(r'^archive/all/$', views.ArchivedMessagesView.as_view(), {'one_page': True},
        name='privmsg-archive-all'),
    url(r'^trash/$', views.TrashedMessagesView.as_view(),
        name='privmsg-trash'),
    url(r'^trash/(?P<page>\d+)/$', views.TrashedMessagesView.as_view(),
        name='privmsg-trash-page'),
    url(r'^trash/all/$', views.TrashedMessagesView.as_view(), {'one_page': True},
        name='privmsg-trash-all'),
    url(r'^sent/$', views.SentMessagesView.as_view(),
        name='privmsg-sent'),
    url(r'^sent/(?P<page>\d+)/$', views.SentMessagesView.as_view(),
        name='privmsg-sent-page'),
    url(r'^sent/all/$', views.SentMessagesView.as_view(), {'one_page': True},
        name='privmsg-sent-all'),
    url(r'^read/$', views.ReadMessagesView.as_view(),
        name='privmsg-read'),
    url(r'^read/(?P<page>\d+)/$', views.ReadMessagesView.as_view(),
        name='privmsg-read-page'),
    url(r'^read/all/$', views.ReadMessagesView.as_view(), {'one_page': True},
        name='privmsg-read-all'),
    url(r'^unread/$', views.UnreadMessagesView.as_view(),
        name='privmsg-unread'),
    url(r'^unread/(?P<page>\d+)/$', views.UnreadMessagesView.as_view(),
        name='privmsg-unread-page'),
    url(r'^unread/all/$', views.UnreadMessagesView.as_view(), {'one_page': True},
        name='privmsg-unread-all'),

    # compose views
    url(r'^(?P<pk>\d+)/reply/$', views.MessageReplyView.as_view(),
        name='privmsg-message-reply'),
    url(r'^(?P<pk>\d+)/reply/all/$', views.MessageReplyView.as_view(), {'reply_to_all': True},
        name='privmsg-message-reply-all'),
    url(r'^(?P<pk>\d+)/forward/(?P<user>[^/]+)/$', views.MessageForwardView.as_view(),
        name='privmsg-message-forward-user'),
    url(r'^(?P<pk>\d+)/forward/$', views.MessageForwardView.as_view(),
        name='privmsg-message-forward'),
    url(r'^compose/(?P<user>[^/]+)/$', views.MessageComposeView.as_view(),
        name='privmsg-compose-user'),
    url(r'^compose/$', views.MessageComposeView.as_view(),
        name='privmsg-compose'),

    # message views
    url(r'^(?P<pk>\d+)/archive/$', views.MessageToArchiveView.as_view(),
        name='privmsg-message-archive'),
    url(r'^(?P<pk>\d+)/delete/$', views.MessageDeleteView.as_view(),
        name='privmsg-message-delete'),
    url(r'^(?P<pk>\d+)/trash/$', views.MessageToTrashView.as_view(),
        name='privmsg-message-trash'),
    url(r'^(?P<pk>\d+)/restore/$', views.MessageRestoreView.as_view(),
        name='privmsg-message-restore'),
    url(r'^(?P<pk>\d+)/$', views.MessageView.as_view(),
        name='privmsg-message'),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns.append(
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )

handler404 = 'inyoka.utils.http.global_not_found'
