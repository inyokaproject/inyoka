# -*- coding: utf-8 -*-
"""
    inyoka.planet.urls
    ~~~~~~~~~~~~~~~~~~

    URL list for the planet.

    :copyright: (c) 2007-2020 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.conf import settings
from django.conf.urls import include, url

from . import views

urlpatterns = [
    url(r'^$', views.index),
    url(r'^(\d+)/$', views.index),
    url(r'^hide/(?P<id>\d+)/$', views.hide_entry),
    url(r'^suggest/$', views.suggest),
    url(r'^feeds/(?P<mode>[a-z]+)/(?P<count>\d+)/$', views.feed),
    url(r'^blogs/$', views.blog_list),
    url(r'^blogs/(?P<page>\d)/$', views.blog_list),
    url(r'^blogs/export/(?P<export_type>[a-z]+)/$', views.export),
    url(r'^blog/new/$', views.blog_edit),
    url(r'^blog/(?P<blog>\d+)/edit/$', views.blog_edit),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns.append(
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )

handler404 = 'inyoka.utils.http.global_not_found'
handler500 = 'inyoka.utils.http.server_error'
