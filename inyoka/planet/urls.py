"""
    inyoka.planet.urls
    ~~~~~~~~~~~~~~~~~~

    URL list for the planet.

    :copyright: (c) 2007-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.conf import settings
from django.urls import include, path, re_path
from django.views.decorators.cache import cache_page

from ..utils.http import (
    bad_request_view,
    global_not_found,
    permission_denied_view,
    server_error,
)
from . import views

urlpatterns = [
    path('', views.index),
    re_path(r'^(\d+)/$', views.index),
    path('hide/<int:id>/', views.hide_entry),
    path('suggest/', views.suggest),
    re_path(r'^feeds/(?P<mode>[a-z]+)/(?P<count>\d+)/$', cache_page(60 * 5)(views.PlanetAtomFeed())),
    path('blogs/', views.blog_list),
    re_path(r'^blogs/(?P<page>\d)/$', views.blog_list),
    re_path(r'^blogs/export/(?P<export_type>[a-z]+)/$', views.export),
    path('blog/new/', views.blog_edit),
    path('blog/<int:blog>/edit/', views.blog_edit),
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
