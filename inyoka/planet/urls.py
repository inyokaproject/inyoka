# -*- coding: utf-8 -*-
"""
    inyoka.planet.urls
    ~~~~~~~~~~~~~~~~~~

    URL list for the planet.

    :copyright: (c) 2007-2014 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.conf.urls import patterns

urlpatterns = patterns('inyoka.planet.views',
    (r'^$', 'index'),
    (r'^(\d+)/$', 'index'),
    (r'^hide/(?P<id>\d+)/$', 'hide_entry'),
    (r'^suggest/$', 'suggest'),
    (r'^feeds/(?P<mode>[a-z]+)/(?P<count>\d+)/$', 'feed'),
    (r'^blogs/$', 'blog_list'),
    (r'^blogs/(?P<page>\d)/$', 'blog_list'),
    (r'^blogs/export/(?P<export_type>[a-z]+)/$', 'export'),
    (r'^blog/new/$', 'blog_edit'),
    (r'^blog/(?P<blog>\d+)/edit/$', 'blog_edit'),
)


handler404 = 'inyoka.utils.http.global_not_found'
