"""
    inyoka.utils.services
    ~~~~~~~~~~~~~~~~~~~~~

    This module implements a simple dispatcher for services.  Applications
    can still write their own but for 99% of the time this should work.


    :copyright: (c) 2007-2023 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.http import Http404


class SimpleDispatcher:
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


def never_cache(view_func):
    view_func.__never__cache__ = True
    return view_func
