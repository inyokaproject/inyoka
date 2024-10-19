"""
    inyoka.media_urls
    ~~~~~~~~~~~~~~~~~

    URL list for media files.

    :copyright: (c) 2007-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.conf import settings
from django.urls import include, path, re_path
from django.views.static import serve as view

from inyoka.utils.http import (
    bad_request_view,
    global_not_found,
    permission_denied_view,
    server_error,
)

urlpatterns = [
    re_path(r'^(?P<path>.*)$', view, {'document_root': settings.MEDIA_ROOT}),
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
