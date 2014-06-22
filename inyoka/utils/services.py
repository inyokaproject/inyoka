# -*- coding: utf-8 -*-
"""
    inyoka.utils.services
    ~~~~~~~~~~~~~~~~~~~~~

    This module implements a simple dispatcher for services.  Applications
    can still write their own but for 99% of the time this should work.


    :copyright: (c) 2007-2014 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from itertools import imap

from django.http import Http404, HttpResponseNotAllowed

from inyoka.utils.decorators import patch_wrapper


class SimpleDispatcher(object):
    """
    A very basic dispatcher.
    """

    def __init__(self, **methods):
        self.methods = methods

    def register(self, name=None):
        def decorator(f):
            service_name = name or f.__name__
            self.methods[service_name] = f
        return decorator

    def __call__(self, request, name):
        if name not in self.methods:
            return Http404('Service not found.')
        return self.methods[name](request)


def permit_methods(methods=('GET',)):
    """Helper method to only permit a few HTTP Methods"""
    def decorate(func):
        def oncall(request, *args, **kwargs):
            if not request.method.lower() in imap(str.lower, methods):
                return HttpResponseNotAllowed(methods)
            return func(request, *args, **kwargs)
        return patch_wrapper(oncall, func)
    return decorate


def never_cache(view_func):
    view_func.__never__cache__ = True
    return view_func
