"""
    inyoka.utils.decorators
    ~~~~~~~~~~~~~~~~~~~~~~~

    Decorators and decorator helpers.

    :copyright: (c) 2007-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""


def patch_wrapper(decorator, base):
    decorator.__name__ = base.__name__
    decorator.__module__ = base.__module__
    decorator.__doc__ = base.__doc__
    decorator.__dict__ = base.__dict__
    return decorator


class deferred:
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
        for key, value in obj.__class__.__dict__.items():
            if getattr(value, '__class__', None) is deferred:
                try:
                    delattr(obj, key)
                except AttributeError:
                    continue
