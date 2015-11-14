# -*- coding: utf-8 -*-
"""
    inyoka.pastebin.urls
    ~~~~~~~~~~~~~~~~~~~~

    The urls for the pastebin service.

    :copyright: (c) 2007-2015 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.conf import settings
from django.conf.urls import include, patterns, url

urlpatterns = patterns('inyoka.pastebin.views',
    (r'^$', 'browse'),
    (r'^(\d+)/$', 'display'),
    (r'^raw/(\d+)/$', 'raw'),
    (r'^delete/(\d+)/$', 'delete'),
    (r'^add/$', 'add'),
)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += patterns('',
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )

handler404 = 'inyoka.utils.http.global_not_found'
