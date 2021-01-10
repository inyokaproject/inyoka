# -*- coding: utf-8 -*-
"""
    inyoka.portal.urls
    ~~~~~~~~~~~~~~~~~~

    The urls for the main portal (index page, error pages, login page etc.)

    :copyright: (c) 2007-2021 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.conf import settings
from django.conf.urls import include, url

from . import views
from ..utils.http import global_not_found, server_error

urlpatterns = [
    url(r'^$', views.index),
    url(r'^login/$', views.login),
    url(r'^logout/$', views.logout),
    url(r'^users/$', views.memberlist),
    url(r'^users/(?P<page>\d+)/$', views.memberlist),
    url(r'^user/new/$', views.user_new),
    url(r'^user/(?P<username>[^/]+)/$', views.profile),
    url(r'^user/(?P<username>[^/]+)/subscribe/$', views.subscribe_user),
    url(r'^user/(?P<username>[^/]+)/unsubscribe/$', views.unsubscribe_user),
    url(r'^user/(?P<username>[^/]+)/edit/$', views.user_edit),
    url(r'^user/(?P<username>[^/]+)/edit/profile/$', views.user_edit_profile),
    url(r'^user/(?P<username>[^/]+)/edit/settings/$', views.user_edit_settings),
    url(r'^user/(?P<username>[^/]+)/edit/groups/$', views.user_edit_groups),
    url(r'^user/(?P<username>[^/]+)/edit/status/$', views.user_edit_status),
    url(r'^user/(?P<username>[^/]+)/mail/$', views.user_mail),
    url(r'^users/resend_activation_mail/$', views.admin_resend_activation_mail),
    url(r'^groups/$', views.grouplist),
    url(r'^groups/(?P<page>\d+)/$', views.grouplist),
    url(r'^group/new/$', views.group_new),
    url(r'^group/(?P<name>[^/]+)/$', views.group),
    url(r'^group/(?P<name>[^/]+)/edit/$', views.group_edit),
    url(r'^group/(?P<name>[^/]+)/edit/global_permissions/$', views.group_edit_global_permissions),
    url(r'^group/(?P<name>[^/]+)/edit/forum_permissions/$', views.group_edit_forum_permissions),
    url(r'^group/(?P<name>[^/]+)/(?P<page>\d+)/$', views.group),
    url(r'^usercp/$', views.usercp),
    url(r'^usercp/settings/$', views.usercp_settings),
    url(r'^usercp/profile/$', views.usercp_profile),
    url(r'^usercp/password/$', views.usercp_password),
    url(r'^usercp/subscriptions/$', views.usercp_subscriptions),
    url(r'^usercp/subscriptions/(?P<page>\d+)/$', views.usercp_subscriptions),
    url(r'^usercp/deactivate/$', views.usercp_deactivate),
    url(r'^privmsg/$', views.privmsg),
    url(r'^privmsg/new/$', views.privmsg_new),
    url(r'^privmsg/new/(?P<username>.+)/$', views.privmsg_new),
    url(r'^privmsg/(?P<folder>[a-z]+)/$', views.privmsg),
    url(r'^privmsg/(?P<folder>[a-z]+)/page/$', views.privmsg),
    url(r'^privmsg/(?P<folder>[a-z]+)/page/(?P<page>\d+)/$', views.privmsg),
    url(r'^privmsg/(?P<folder>[a-z]+)/all/$', views.privmsg, {'one_page': True}),
    url(r'^privmsg/(?P<entry_id>\d+)/$', views.privmsg),
    url(r'^privmsg/(?P<folder>[a-z]+)/(?P<entry_id>\d+)/$', views.privmsg),
    url(r'^map/$', views.usermap),
    url(r'^whoisonline/$', views.whoisonline),
    url(r'^inyoka/$', views.about_inyoka),
    url(r'^register/$', views.register),
    url(r'^(?P<action>activate|delete)/(?P<username>[^/]+)/(?P<activation_key>.*?)/$', views.activate),
    url(r'^confirm/(?P<action>reactivate_user|set_new_email|reset_email)/$', views.confirm),
    url(r'^lost_password/$', views.lost_password),
    url(r'^lost_password/(?P<uidb36>[0-9A-Za-z]{1,13})/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', views.set_new_password),
    url(r'^feeds/$', views.feedselector),
    url(r'^feeds/(?P<app>[^/]+)/$', views.feedselector),
    url(r'^calendar/$', views.calendar_overview),
    url(r'^calendar/(?P<year>\d{4})/(?P<month>(0?\d|1[0-2]))/$', views.calendar_month),
    url(r'^calendar/(?P<slug>.*?)/ics/$', views.calendar_ical),
    url(r'^calendar/(?P<slug>.*?)/$', views.calendar_detail),
    url(r'^config/$', views.config),
    url(r'^linkmap/$', views.linkmap_edit),
    url(r'^linkmap/export/$', views.linkmap_export),
    # shortcuts
    url(r'^ikhaya/(\d+)/$', views.ikhaya_redirect),
    # static files
    url(r'^files/$', views.files),
    url(r'^files/(?P<page>\d+)/$', views.files),
    url(r'^files/new/$', views.file_edit),
    url(r'^files/(?P<file>.+)/edit/$', views.file_edit),
    url(r'^files/(?P<slug>.+)/delete/$', views.file_delete),
    # static pages
    url(r'^pages/$', views.pages),
    url(r'^page/new/$', views.page_edit),
]

urlpatterns.extend([
    url(r'^([^/]+)/$', views.static_page),
    url(r'^([^/]+)/edit/$', views.page_edit),
    url(r'^(?P<pk>[^/]+)/delete/$', views.page_delete),
])

if settings.DEBUG:
    import debug_toolbar
    urlpatterns.append(
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )

handler404 = global_not_found
handler500 = server_error
