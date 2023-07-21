# -*- coding: utf-8 -*-
"""
    inyoka.media_urls
    ~~~~~~~~~~~~~~~~~

    URL list for media files.

    :copyright: (c) 2007-2023 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.conf import settings
from django.conf.urls import include, url
from django.views.static import serve as view

from inyoka.utils.http import global_not_found, server_error

urlpatterns = [
    url(r'^(?P<path>.*)$', view, {'document_root': settings.MEDIA_ROOT}),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns.append(
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )

handler404 = global_not_found
handler500 = server_error
