# -*- coding: utf-8 -*-
"""
    inyoka.static_urls
    ~~~~~~~~~~~~~~~~~~

    URL list for static files.

    :copyright: (c) 2007-2017 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^(?P<path>.*)$', 'django.contrib.staticfiles.views.serve',
        {'insecure': True}),
)


handler404 = 'inyoka.utils.http.global_not_found'
