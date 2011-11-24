# -*- coding: utf-8 -*-
"""
    inyoka.static_urls
    ~~~~~~~~~~~~~~~~~~

    URL list for static files.

    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from django.conf.urls.defaults import patterns, url

js_info_dict = {
    'packages': ('inyoka.portal', 'inyoka.wiki', 'inyoka.pastebin',
                 'inyoka.ikhaya', 'inyoka.planet', 'inyoka.forum'),
}

urlpatterns = patterns('',
    url(r'jsi18n$', 'django.views.i18n.javascript_catalog', js_info_dict),
    url(r'^(?P<path>.*)$', 'django.contrib.staticfiles.views.serve',
        {'insecure': True}),
)


handler404 = 'inyoka.utils.urls.global_not_found'
