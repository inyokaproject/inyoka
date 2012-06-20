# -*- coding: utf-8 -*-
"""
    inyoka.utils.decorators
    ~~~~~~~~~~~~~~~~~~~~~~~

    Decorators and decorator helpers.

    :copyright: (c) 2007-2012 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""

from inyoka.utils.local import current_request
from django.utils.translation import get_language_from_request
from django.conf import settings

def patch_wrapper(decorator, base):
    decorator.__name__ = base.__name__
    decorator.__module__ = base.__module__
    decorator.__doc__ = base.__doc__
    decorator.__dict__ = base.__dict__
    return decorator


class deferred(object):
    """
    Deferred properties.  Calculated once and then it replaces the
    property object.
    """

    def __init__(self, func, name=None):
        self.func = func
        self.__name__ = name or func.__name__
        self.__module__ = func.__module__
        self.__doc__ = func.__doc__

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        value = self.func(obj)
        setattr(obj, self.__name__, value)
        return value

    @staticmethod
    def clear(obj):
        """Clear all deferred objects on that class."""
        for key, value in obj.__class__.__dict__.iteritems():
            if getattr(value, '__class__', None) is deferred:
                try:
                    delattr(obj, key)
                except AttributeError:
                    continue


class try_localflavor(object):
    """ Search for localized versions of this function before calling it """
    def __init__(self, func):
        self.func = func
        self.__name__ = func.__name__
        self.__module__ = func.__module__
        self.__doc__ = func.__doc__

    def __call__(self, *args, **kwargs):
        # determine current language
        ## Use this if dynamic language detection (LocaleMiddleware) is activated
        # request = current_request._get_current_object()
        # language = request.LANGUAGE_CODE[0:2]
        ## This uses static language detection
        # language = settings.LANGUAGE_CODE[0:2]
        ## This uses gettext language detection
        request = current_request._get_current_object()
        language = get_language_from_request(request).lower()[0:2]

        try:
            module = __import__("inyoka.utils.localflavor.%s.%s" %
                                (language, self.__module__.split('.')[-1]),
                                globals(), locals(), self.__name__)
            if self.__name__ in dir(module):
                localized_func = getattr(module, self.__name__)
                return localized_func(*args, **kwargs)
        except ImportError:
            pass

        return self.func(*args, **kwargs)


