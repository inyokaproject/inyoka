# -*- coding: utf-8 -*-
"""
    inyoka.pastebin.urls
    ~~~~~~~~~~~~~~~~~~~~

    The urls for the pastebin service.

    :copyright: (c) 2007-2015 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.conf.urls import patterns
from django.views.generic import RedirectView

urlpatterns = patterns('inyoka.pastebin.views',
    (r'^$', 'browse'),
    (r'^(\d+)/$', 'display'),
    (r'^raw/(\d+)/$', 'raw'),
    (r'^browse/$', RedirectView.as_view(url='/')),
    (r'^delete/(\d+)/$', 'delete'),
    (r'^add/$', 'add'),
)


handler404 = 'inyoka.utils.http.global_not_found'
