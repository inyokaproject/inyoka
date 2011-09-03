# -*- coding: utf-8 -*-
"""
    inyoka.utils.legacyurls
    ~~~~~~~~~~~~~~~~~~~~~~~

    Support module for legacy url handling.

    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import re
from django.core.exceptions import ObjectDoesNotExist
from inyoka.utils.http import HttpResponsePermanentRedirect


def test_legacy_url(request, test_func):
    """
    This function currently does nothing but invoking the test function
    and if that one returns a url it returns a redirect response.  We
    could use this to add additional logging here.
    """
    old_url = test_func(request.path, request.GET)
    if old_url is not None:
        return HttpResponsePermanentRedirect(old_url)


class LegacyDispatcher(object):
    """Helper class for legacy URLs."""

    def __init__(self):
        self.regexes = []

    def __call__(self, path, args):
        for regex, handler in self.regexes:
            match = regex.search(path)
            if match is not None:
                try:
                    rv = handler(args, match, *match.groups())
                    if rv is not None:
                        return rv
                except ObjectDoesNotExist:
                    return

    def url(self, rule):
        def proxy(f):
            self.regexes.append((re.compile(rule), f))
            return f
        return proxy

    def tester(self, request):
        return test_legacy_url(request, self)
