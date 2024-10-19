"""
    inyoka.portal.urls
    ~~~~~~~~~~~~~~~~~~

    The urls for the main portal (index page, error pages, login page etc.)

    :copyright: (c) 2007-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.conf import settings
from django.urls import include, path, re_path

from ..utils.http import (
    bad_request_view,
    global_not_found,
    permission_denied_view,
    server_error,
)
from . import views

urlpatterns = [
    path('', views.index),
    path('login/', views.login),
    path('logout/', views.logout),
    path('users/', views.memberlist),
    path('users/<int:page>/', views.memberlist),
    path('user/new/', views.user_new),
    path('user/<str:username>/', views.profile),
    path('user/<str:username>/subscribe/', views.subscribe_user),
    path('user/<str:username>/unsubscribe/', views.unsubscribe_user),
    path('user/<str:username>/edit/', views.user_edit),
    path('user/<str:username>/edit/profile/', views.user_edit_profile),
    path('user/<str:username>/edit/settings/', views.user_edit_settings),
    path('user/<str:username>/edit/groups/', views.user_edit_groups),
    path('user/<str:username>/edit/status/', views.user_edit_status),
    path('user/<str:username>/mail/', views.user_mail),
    path('users/resend_activation_mail/', views.admin_resend_activation_mail),
    path('groups/', views.grouplist),
    path('groups/<int:page>/', views.grouplist),
    path('group/new/', views.group_new),
    path('group/<str:name>/', views.group),
    path('group/<str:name>/edit/', views.group_edit),
    path('group/<str:name>/edit/global_permissions/', views.group_edit_global_permissions),
    path('group/<str:name>/edit/forum_permissions/', views.group_edit_forum_permissions),
    path('group/<str:name>/<int:page>/', views.group),
    path('usercp/', views.usercp),
    path('usercp/settings/', views.usercp_settings),
    path('usercp/profile/', views.usercp_profile),
    path('usercp/password/', views.InyokaPasswordChangeView.as_view()),
    path('usercp/subscriptions/', views.usercp_subscriptions),
    path('usercp/subscriptions/<int:page>/', views.usercp_subscriptions),
    path('usercp/deactivate/', views.usercp_deactivate),
    path('privmsg/', views.privmsg),
    path('privmsg/new/', views.privmsg_new),
    path('privmsg/new/<str:username>/', views.privmsg_new),
    re_path(r'^privmsg/(?P<folder>[a-z]+)/$', views.privmsg),
    re_path(r'^privmsg/(?P<folder>[a-z]+)/page/$', views.privmsg),
    re_path(r'^privmsg/(?P<folder>[a-z]+)/page/(?P<page>\d+)/$', views.privmsg),
    re_path(r'^privmsg/(?P<folder>[a-z]+)/all/$', views.privmsg, {'one_page': True}),
    path('privmsg/<int:entry_id>/', views.privmsg),
    re_path(r'^privmsg/(?P<folder>[a-z]+)/(?P<entry_id>\d+)/$', views.privmsg),
    path('map/', views.usermap),
    path('whoisonline/', views.whoisonline),
    path('inyoka/', views.about_inyoka),
    path('register/', views.register),
    re_path(r'^(?P<action>activate|delete)/(?P<username>[^/]+)/(?P<activation_key>.*?)/$', views.activate),
    re_path(r'^confirm/(?P<action>reactivate_user|set_new_email|reset_email)/$', views.confirm),
    path('lost_password/', views.InyokaPasswordResetView.as_view()),
    re_path(r'^lost_password/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$', views.InyokaPasswordResetConfirmView.as_view()),
    path('feeds/', views.feedselector),
    path('feeds/<str:app>/', views.feedselector),
    path('calendar/', views.calendar_overview),
    re_path(r'^calendar/(?P<year>\d{4})/(?P<month>(0?\d|1[0-2]))/$', views.calendar_month),
    re_path(r'^calendar/(?P<slug>.*?)/ics/$', views.calendar_ical),
    re_path(r'^calendar/(?P<slug>.*?)/$', views.calendar_detail),
    path('config/', views.config),
    path('linkmap/', views.linkmap_edit),
    path('linkmap/export/', views.linkmap_export),
    # shortcuts
    re_path(r'^ikhaya/(\d+)/$', views.ikhaya_redirect),
    # static files
    path('files/', views.files),
    path('files/<int:page>/', views.files),
    path('files/new/', views.file_edit),
    path('files/<path:file>/edit/', views.file_edit),
    path('files/<path:slug>/delete/', views.file_delete),
    # static pages
    path('pages/', views.pages),
    path('page/new/', views.page_edit),
]

urlpatterns.extend([
    re_path(r'^([^/]+)/$', views.static_page),
    re_path(r'^([^/]+)/edit/$', views.page_edit),
    path('<str:pk>/delete/', views.page_delete),
])

if settings.DEBUG:
    import debug_toolbar
    urlpatterns.append(
        path('__debug__/', include(debug_toolbar.urls)),
    )

handler400 = bad_request_view
handler403 = permission_denied_view
handler404 = global_not_found
handler500 = server_error
