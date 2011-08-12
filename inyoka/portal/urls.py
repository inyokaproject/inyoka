# -*- coding: utf-8 -*-
"""
    inyoka.portal.urls
    ~~~~~~~~~~~~~~~~~~

    The urls for the main portal (index page, error pages, login page etc.)

    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from django.conf.urls.defaults import patterns

urlpatterns = patterns('inyoka.portal.views',
    (r'^$', 'index'),
    (r'^404/$', 'not_found'),
    (r'^markup.css', 'markup_styles'),
    (r'^login/$', 'login'),
    (r'^logout/$', 'logout'),
    (r'^search/$', 'search'),
    (r'^users/$', 'memberlist'),
    (r'^users/(?P<page>\d+)/$', 'memberlist'),
    (r'^user/new/$', 'user_new'),
    (r'^user/(?P<username>[^/]+)/$', 'profile'),
    (r'^user/(?P<username>[^/]+)/subscribe/$', 'subscribe_user'),
    (r'^user/(?P<username>[^/]+)/unsubscribe/$', 'unsubscribe_user'),
    (r'^user/(?P<username>[^/]+)/edit/$', 'user_edit'),
    (r'^user/(?P<username>[^/]+)/edit/profile/$', 'user_edit_profile'),
    (r'^user/(?P<username>[^/]+)/edit/settings/$', 'user_edit_settings'),
    (r'^user/(?P<username>[^/]+)/edit/groups/$', 'user_edit_groups'),
    (r'^user/(?P<username>[^/]+)/edit/privileges/$', 'user_edit_privileges'),
    (r'^user/(?P<username>[^/]+)/edit/password/$', 'user_edit_password'),
    (r'^user/(?P<username>[^/]+)/edit/status/$', 'user_edit_status'),
    (r'^user/(?P<username>[^/]+)/mail/$', 'user_mail'),
    (r'^users/resend_activation_mail/$', 'admin_resend_activation_mail'),
    (r'^users/special_rights/$', 'users_with_special_rights'),
    (r'^groups/$', 'grouplist'),
    (r'^groups/(?P<page>\d+)/$', 'grouplist'),
    (r'^group/new/$', 'group_edit'),
    (r'^group/(?P<name>[^/]+)/$', 'group'),
    (r'^group/(?P<name>[^/]+)/edit/$', 'group_edit'),
    (r'^group/(?P<name>[^/]+)/(?P<page>\d+)/$', 'group'),
    (r'^usercp/$', 'usercp'),
    (r'^usercp/settings/$', 'usercp_settings'),
    (r'^usercp/profile/$', 'usercp_profile'),
    (r'^usercp/password/$', 'usercp_password'),
    (r'^usercp/subscriptions/$', 'usercp_subscriptions'),
    (r'^usercp/subscriptions/(?P<page>\d+)/$', 'usercp_subscriptions'),
    (r'^usercp/deactivate/$', 'usercp_deactivate'),
    (r'^usercp/userpage/$', 'usercp_userpage'),
    (r'^privmsg/$', 'privmsg'),
    (r'^privmsg/new/$', 'privmsg_new'),
    (r'^privmsg/new/(?P<username>.+)/$', 'privmsg_new'),
    (r'^privmsg/(?P<folder>[a-z]+)/$', 'privmsg'),
    (r'^privmsg/(?P<folder>[a-z]+)/page/$', 'privmsg'),
    (r'^privmsg/(?P<folder>[a-z]+)/page/(?P<page>\d+)/$', 'privmsg'),
    (r'^privmsg/(?P<entry_id>\d+)/$', 'privmsg'),
    (r'^privmsg/(?P<folder>[a-z]+)/(?P<entry_id>\d+)/$', 'privmsg'),
    (r'^map/$', 'usermap'),
    (r'^whoisonline/$', 'whoisonline'),
    (r'^inyoka/$', 'about_inyoka'),
    (r'^register/$', 'register'),
    (r'^(?P<action>activate|delete)/(?P<username>[^/]+)/(?P<activation_key>.*?)/$', 'activate'),
    (r'^register/resend/(?P<username>[^/]+)/$', 'resend_activation_mail'),
    (r'^lost_password/$', 'lost_password'),
    (r'^lost_password/(?P<username>[^/]+)/(?P<new_password_key>[a-z0-9]+)/$', 'set_new_password'),
    (r'^confirm/$', 'confirm'),
    (r'^confirm/(?P<action>[^/]+)/$', 'confirm'),
    (r'^usercp/reactivate/$', 'confirm', {'action':'reactivate_user'}),
    # ^ legacy support, can be removed after september 15th
    (r'^feeds/$', 'feedselector'),
    (r'^feeds/(?P<app>[^/]+)/$', 'feedselector'),
    (r'^calendar/$', 'calendar_overview'),
    (r'^calendar/(?P<year>\d{4})/(?P<month>(0?\d|1[0-2]))/$', 'calendar_month'),
    (r'^calendar/(?P<slug>.*?)/$', 'calendar_detail'),
    (r'^opensearch/(?P<app>[a-z]+)/$', 'open_search'),
    (r'^openid/(.*)', 'openid_consumer'),
    (r'^config/$', 'config'),
    (r'^styles/$', 'styles'),
    # static pages
    (r'^files/$', 'files'),
    (r'^files/(?P<page>\d+)/$', 'files'),
    (r'^files/new/$', 'file_edit'),
    (r'^files/(?P<file>.+)/edit/$', 'file_edit'),
    (r'^files/(?P<slug>.+)/delete/$', 'file_delete'),
    (r'^pages/$', 'pages'),
    (r'^page/new/$', 'page_edit'),
    (r'^([-A-Za-z_]+)/$', 'static_page'),
    (r'^([-A-Za-z_]+)/edit/$', 'page_edit'),
    (r'^(?P<pk>[-A-Za-z_]+)/delete/$', 'page_delete'),
)


handler404 = 'inyoka.portal.views.not_found'
