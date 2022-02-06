# -*- coding: utf-8 -*-
"""
    inyoka.hosts
    ~~~~~~~~~~~~

    Subdomain specifications.

    :copyright: (c) 2007-2022 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import sys

from django.conf import settings
from django.http import HttpResponsePermanentRedirect

from django_hosts import host, patterns


def redirect_www(request):
    """Redirects www. to settings.BASE_DOMAIN_NAME"""
    host = request.get_host()[4:]
    return HttpResponsePermanentRedirect('//%s%s' % (host, request.path))


# names refer to our app names (used in utils.urls)!
# regex has to be a simple name (again due to utils.urls)!
host_patterns = patterns('',
    host('www', settings.ROOT_URLCONF, name='www', callback=redirect_www),
    host('', settings.ROOT_URLCONF, name='portal'),
    host('planet', 'inyoka.planet.urls', name='planet'),
    host('ikhaya', 'inyoka.ikhaya.urls', name='ikhaya'),
    host('wiki', 'inyoka.wiki.urls', name='wiki'),
    host('paste', 'inyoka.pastebin.urls', name='pastebin'),
    host('forum', 'inyoka.forum.urls', name='forum'),
)

if settings.INYOKA_HOST_STATICS:
    host_patterns += patterns('',
        host('static', 'inyoka.static_urls', name='static'),
        host('media', 'inyoka.media_urls', name='media'),
    )
