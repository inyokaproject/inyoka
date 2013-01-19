# -*- coding: utf-8 -*-
"""
    inyoka.media_urls
    ~~~~~~~~~~~~~~~~~

    URL list for media files.

    :copyright: (c) 2007-2013 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from django.conf.urls import patterns, url
from django.conf import settings


urlpatterns = patterns('',
    url(r'^(?P<path>.*)$', 'django.views.static.serve', {
        'document_root': settings.MEDIA_ROOT,
    }),
)


handler404 = 'inyoka.utils.urls.global_not_found'
