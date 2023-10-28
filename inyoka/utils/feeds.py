"""
    inyoka.utils.feeds
    ~~~~~~~~~~~~~~~~~~~

    Utils for creating an atom feed.  This module relies on
    :mod:`werkzeug.contrib.atom`.

    :copyright: (c) 2007-2023 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.conf import settings
from django.http import Http404, HttpResponse
from django.utils.cache import patch_response_headers
from django.utils.encoding import force_str
from werkzeug.contrib.atom import AtomFeed

MODES = frozenset(('full', 'short', 'title'))


def atom_feed(name=None, supports_modes=True):
    def _wrapper(func):
        def real_func(*args, **kwargs):
            if supports_modes and kwargs.get('mode') not in MODES:
                raise Http404()

            kwargs['count'] = count = int(kwargs['count'])
            try:
                available = settings.AVAILABLE_FEED_COUNTS[name]
            except KeyError:
                raise Http404()

            count = count if count <= max(available) else max(available)
            kwargs['count'] = count

            if count not in available:
                raise Http404()

            rv = func(*args, **kwargs)
            if not isinstance(rv, AtomFeed):
                # ret is a HttpResponse object
                return rv
            content = rv.to_string()
            content_type = 'application/atom+xml; charset=utf-8'
            response = HttpResponse(content, content_type=content_type)
            patch_response_headers(response, 60 * 30)
            return response
        return real_func
    return _wrapper


class AtomFeed(AtomFeed):
    def to_string(self):
        ret = []
        for item in self.generate():
            ret.append(force_str(item))
        return ''.join(ret)
