# -*- coding: utf-8 -*-
"""
    inyoka.portal.urls
    ~~~~~~~~~~~~~~~~~~

    The urls for the main portal (index page, error pages, login page etc.)

    :copyright: (c) 2007-2016 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.conf.urls import url, include
from django.views.i18n import javascript_catalog

from . import views

urlpatterns = [
    url(r'^$', views.index),
    url(r'^markup.css', views.markup_styles),
    url(r'^login/$', views.login, name='login'),
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
    url(r'^user/(?P<username>[^/]+)/edit/privileges/$', views.user_edit_privileges),
    url(r'^user/(?P<username>[^/]+)/edit/status/$', views.user_edit_status),
    url(r'^user/(?P<username>[^/]+)/mail/$', views.user_mail),
    url(r'^users/resend_activation_mail/$', views.admin_resend_activation_mail),
    url(r'^users/special_rights/$', views.users_with_special_rights),
    url(r'^groups/$', views.grouplist),
    url(r'^groups/(?P<page>\d+)/$', views.grouplist),
    url(r'^group/new/$', views.group_edit),
    url(r'^group/(?P<name>[^/]+)/$', views.group),
    url(r'^group/(?P<name>[^/]+)/edit/$', views.group_edit),
    url(r'^group/(?P<name>[^/]+)/(?P<page>\d+)/$', views.group),
    url(r'^usercp/$', views.usercp),
    url(r'^usercp/settings/$', views.usercp_settings),
    url(r'^usercp/profile/$', views.usercp_profile),
    url(r'^usercp/password/$', views.usercp_password),
    url(r'^usercp/subscriptions/$', views.usercp_subscriptions),
    url(r'^usercp/subscriptions/(?P<page>\d+)/$', views.usercp_subscriptions),
    url(r'^usercp/deactivate/$', views.usercp_deactivate),
    url(r'^map/$', views.usermap),
    url(r'^whoisonline/$', views.whoisonline),
    url(r'^inyoka/$', views.about_inyoka),
    url(r'^register/$', views.register),
    url(r'^(?P<action>activate|delete)/(?P<username>[^/]+)/(?P<activation_key>.*?)/$', views.activate),
    url(r'^register/resend/(?P<username>[^/]+)/$', views.resend_activation_mail),
    url(r'^confirm/(?P<action>reactivate_user|set_new_email|reset_email)/$', views.confirm),
    url(r'^lost_password/$', views.lost_password),
    url(r'^lost_password/(?P<uidb36>[0-9A-Za-z]{1,13})/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', views.set_new_password),
    url(r'^feeds/$', views.feedselector),
    url(r'^feeds/(?P<app>[^/]+)/$', views.feedselector),
    url(r'^calendar/$', views.calendar_overview),
    url(r'^calendar/(?P<year>\d{4})/(?P<month>(0?\d|1[0-2]))/$', views.calendar_month),
    url(r'^calendar/(?P<slug>.*?)/$', views.calendar_detail),
    url(r'^config/$', views.config),
    url(r'^styles/$', views.styles),
    # shortcuts
    url(r'^ikhaya/(\d+)/$', views.ikhaya_redirect),
    # static pages
    url(r'^files/$', views.files),
    url(r'^files/(?P<page>\d+)/$', views.files),
    url(r'^files/new/$', views.file_edit),
    url(r'^files/(?P<file>.+)/edit/$', views.file_edit),
    url(r'^files/(?P<slug>.+)/delete/$', views.file_delete),
    url(r'^pages/$', views.pages),
    url(r'^page/new/$', views.page_edit),
    url(r'^messages/', include('inyoka.privmsg.urls')),
]


js_info_dict = {
    'packages': ('inyoka.portal', 'inyoka.wiki', 'inyoka.pastebin',
                 'inyoka.ikhaya', 'inyoka.planet', 'inyoka.forum'),
}

urlpatterns.append(
    url(r'jsi18n/$', javascript_catalog, js_info_dict)
)

urlpatterns.extend([
    url(r'^([-A-Za-z_]+)/$', views.static_page),
    url(r'^([-A-Za-z_]+)/edit/$', views.page_edit),
    url(r'^(?P<pk>[-A-Za-z_]+)/delete/$', views.page_delete),
])

handler404 = 'inyoka.utils.http.global_not_found'
