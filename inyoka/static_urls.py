"""
    inyoka.static_urls
    ~~~~~~~~~~~~~~~~~~

    URL list for static files.

    :copyright: (c) 2007-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.conf import settings
from django.urls import include, path, re_path
from django.views.static import serve

from inyoka.utils.http import global_not_found, server_error, bad_request_view, \
    permission_denied_view


def view(*args, **kwargs):
    response = serve(*args, **kwargs)
    if settings.DEBUG:
        response['Access-Control-Allow-Origin'] = '*'
    return response

urlpatterns = [
    re_path(r'^(?P<path>.*)$', view, {'document_root': settings.STATIC_ROOT}),
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
