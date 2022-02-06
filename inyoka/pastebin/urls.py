# -*- coding: utf-8 -*-
"""
    inyoka.pastebin.urls
    ~~~~~~~~~~~~~~~~~~~~

    The urls for the pastebin service.

    :copyright: (c) 2007-2022 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.conf import settings
from django.conf.urls import include, url

from . import views
from ..utils.http import global_not_found, server_error

urlpatterns = [
    url(r'^$', views.browse),
    url(r'^(\d+)/$', views.display),
    url(r'^raw/(\d+)/$', views.raw),
    url(r'^delete/(\d+)/$', views.delete),
    url(r'^add/$', views.add),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns.append(
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )

handler404 = global_not_found
handler500 = server_error
