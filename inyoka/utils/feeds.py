# -*- coding: utf-8 -*-
"""
    inyoka.utils.feeds
    ~~~~~~~~~~~~~~~~~~~

    Utils for creating an atom feed.  This module relies in :mod:`werkzeug.contrib.atom`.

    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from werkzeug.contrib.atom import AtomFeed
from django.conf import settings
from django.utils.encoding import force_unicode
from django.utils.cache import patch_response_headers
from inyoka.utils.http import HttpResponse, PageNotFound


def atom_feed(name=None, supports_modes=True):
    def _wrapper(func):
        def real_func(*args, **kwargs):
            if supports_modes and kwargs.get('mode') not in ('full', 'short', 'title'):
                raise PageNotFound()

            kwargs['count'] = count = int(kwargs['count'])
            try:
                available = settings.AVAILABLE_FEED_COUNTS[name]
            except KeyError:
                raise PageNotFound()

            count = count if count <= max(available) else max(available)
            kwargs['count'] = count

            if count not in available:
                raise PageNotFound()

            rv = func(*args, **kwargs)
            if not isinstance(rv, AtomFeed):
                # ret is a HttpResponse object
                return rv
            content = rv.to_string()
            content_type='application/atom+xml; charset=utf-8'
            response = HttpResponse(content, content_type=content_type)
            patch_response_headers(response, 60 * 30)
            return response
        return real_func
    return _wrapper


class AtomFeed(AtomFeed):
    def to_string(self):
        ret = []
        for item in self.generate():
            ret.append(force_unicode(item))
        return u''.join(ret)
