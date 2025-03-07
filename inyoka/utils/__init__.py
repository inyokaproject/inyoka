"""
    inyoka.utils
    ~~~~~~~~~~~~

    Various application independent utilities.

    :copyright: (c) 2007-2025 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import math
from itertools import groupby as igroupby

from django.contrib.contenttypes.models import ContentType


def ctype(model):
    return ContentType.objects.get_for_model(model)


class classproperty:
    """
    A mix out of the built-in `classmethod` and
    `property` so that we can achieve a property
    that is not bound to an instance.

    Example::

        >>> class Foo(object):
        ...     bar = 'baz'
        ...
        ...     @classproperty
        ...     def bars(cls):
        ...         return [cls.bar]
        ...
        >>> Foo.bars
        ['baz']
    """

    def __init__(self, func, name=None):
        self.func = func
        self.__name__ = name or func.__name__
        self.__module__ = func.__module__
        self.__doc__ = func.__doc__

    def __get__(self, desc, cls):
        value = self.func(cls)
        return value


def get_significant_digits(value, lower, upper):
    """Get the significant digits of value which are constrained by the
    (inclusive) lower and upper bounds.

    If there are no significant digits which are definitely within the
    bounds, exactly one significant digit will be returned in the result.

    >>> get_significant_digits(15, 15, 15)
    15
    >>> get_significant_digits(4777, 208, 6000)
    5000
    >>> get_significant_digits(9, 9, 100)
    9

    """
    assert(lower <= value)
    assert(value <= upper)
    diff = upper - lower

    # Get the first power of 10 greater than the difference.
    # This corresponds to the magnitude of the smallest significant digit.
    if diff == 0:
        pos_pow_10 = 1
    else:
        pos_pow_10 = int(10 ** math.ceil(math.log10(diff)))

    # Special case for situation where we don't have any significant digits:
    # get the magnitude of the most significant digit in value.
    if pos_pow_10 > value:
        if value == 0:
            pos_pow_10 = 1
        else:
            pos_pow_10 = int(10 ** math.floor(math.log10(value)))

    # Return the value, rounded to the nearest multiple of pos_pow_10
    return ((value + pos_pow_10 // 2) // pos_pow_10) * pos_pow_10


def groupby(input, keyfunc):
    result = {}
    for key, valuesiter in igroupby(sorted(input, key=keyfunc), keyfunc):
        result[key] = list(v[0] for v in valuesiter)
    return result


def get_request_context(request):
    if not request:
        return None

    mapping = {'ikhaya': 'ikhaya',
               'planet': 'planet',
               'wiki': 'wiki',
               'paste': 'pastebin',
               'forum': 'forum'}

    return mapping.get(request.subdomain, None)
