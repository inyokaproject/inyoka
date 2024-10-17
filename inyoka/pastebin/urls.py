"""
    inyoka.pastebin.urls
    ~~~~~~~~~~~~~~~~~~~~

    The urls for the pastebin service.

    :copyright: (c) 2007-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.conf import settings
from django.urls import include, path, re_path

from ..utils.http import global_not_found, server_error, bad_request_view, \
    permission_denied_view
from . import views

urlpatterns = [
    path('', views.browse),
    re_path(r'^(\d+)/$', views.display),
    re_path(r'^raw/(\d+)/$', views.raw),
    re_path(r'^delete/(\d+)/$', views.delete),
    path('add/', views.add),
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
