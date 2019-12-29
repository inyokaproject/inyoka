# -*- coding: utf-8 -*-
"""
    inyoka.static_urls
    ~~~~~~~~~~~~~~~~~~

    URL list for static files.

    :copyright: (c) 2007-2020 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.conf import settings
from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^(?P<path>.*)$', 'django.contrib.staticfiles.views.serve',
        {'insecure': True}),
)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns.append(
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )


handler404 = 'inyoka.utils.http.global_not_found'
handler500 = 'inyoka.utils.http.server_error'
