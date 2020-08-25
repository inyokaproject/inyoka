# -*- coding: utf-8 -*-
"""
    inyoka.markuptools
    ~~~~~~~~~~~~~~~~~~

    Useful classes for parsers.

    :copyright: (c) 2007-2020 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import sys
from collections import namedtuple

#: Represents one token.
Token = namedtuple('Token', ('type', 'value'))


class TokenStreamIterator(object):
    """
    The iterator for tokenstreams.  Iterate over the stream
    until the eof token is reached.
    """

    def __init__(self, stream):
        self._stream = stream

    def __iter__(self):
        return self

    def __next__(self):
        token = self._stream.current
        if token.type == 'eof':
            raise StopIteration()
        next(self._stream)
        return token


class TokenStream(object):
    """
    A token stream wraps a generator and supports pushing tokens back.
    It also provides some functions to expect tokens and similar stuff.

    Important note: Do never push more than one token back to the
                    stream.  Although the stream object won't stop you
                    from doing so, the behavior is undefined.  Multiple
                    pushed tokens are only used internally!
    """

    def __init__(self, generator):
        self._next = generator.__next__
        self._pushed = []
        self.current = Token('initial', '')
        next(self)

    @classmethod
    def from_tuple_iter(cls, tupleiter):
        return cls(Token(*a) for a in tupleiter)

    def __iter__(self):
        return TokenStreamIterator(self)

    @property
    def eof(self):
        """Are we at the end of the tokenstream?"""
        return not bool(self._pushed) and self.current.type == 'eof'

    def debug(self, stream=None):
        """Displays the tokenized code on the stream provided or stdout."""
        if stream is None:
            stream = sys.stdout
        for token in self:
            stream.write(repr(token) + '\n')

    def look(self):
        """See what's the next token."""
        if self._pushed:
            return self._pushed[-1]
        old_token = self.current
        next(self)
        new_token = self.current
        self.current = old_token
        self.push(new_token)
        return new_token

    def push(self, token, current=False):
        """Push a token back to the stream (only one!)."""
        self._pushed.append(token)
        if current:
            next(self)

    def skip(self, n):
        """Got n tokens ahead."""
        for x in range(n):
            next(self)

    def __next__(self):
        """Go one token ahead."""
        if self._pushed:
            self.current = self._pushed.pop()
        else:
            try:
                self.current = self._next()
            except StopIteration:
                if self.current.type != 'eof':
                    self.current = Token('eof', None)

    def expect(self, type, value=None):
        """expect a given token."""
        assert self.current.type == type
        if value is not None:
            assert self.current.value == value or \
                (value.__class__ is tuple and
                    self.current.value in value), "%s != %s" % (type, value)
        try:
            return self.current
        finally:
            next(self)

    def test(self, type, value=Ellipsis):
        """Test the current token."""
        return self.current.type == type and \
               (value is Ellipsis or self.current.value == value or
                value.__class__ is tuple and
                self.current.value in value)

    def shift(self, token):
        """
        Push one token into the stream.
        """
        old_current = self.current
        next(self)
        self.push(self.current)
        self.push(old_current)
        self.push(token)
        next(self)


def _unpickle_multimap(d):
    """
    Helper that creates a multipmap after pickling.  We need this
    because the default pickle system for dicts requires a mutable
    interface which `MultiMap` is not.  Do not make this a closure
    as this object must be pickleable itself.
    """
    m = dict.__new__(MultiMap)
    dict.__init__(m, d)
    return m


class MultiMap(dict):
    """
    A special structure used to represent metadata and other
    data that has multiple values for one key.
    """
    __slots__ = ()

    def __init__(self, sequence):
        for key, value in sequence:
            dict.setdefault(self, key, []).append(value)

    def _immutable(self, *args):
        raise TypeError('%r instances are immutable' %
                        self.__class__.__name__)

    setlist = setdefault = setlistdefault = update = pop = popitem = \
        poplist = popitemlist = __setitem__ = __delitem__ = _immutable
    del _immutable

    def __getitem__(self, key):
        """Get all values for a key."""
        return dict.get(self, key, [])

    def get(self, key, default=None):
        """Return the first value if the requested data doesn't exist"""
        try:
            return self[key][0]
        except IndexError:
            return default

    def __reduce__(self):
        return (_unpickle_multimap, (dict(self),))

    def __repr__(self):
        tmp = []
        for key, values in self.items():
            for value in values:
                tmp.append((key, value))
        return '%s(%r)' % (self.__class__.__name__, tmp)


def flatten_iterator(iter):
    """Flatten an iterator to one without any sub-elements"""
    for item in iter:
        if hasattr(item, '__iter__'):
            for sub in flatten_iterator(item):
                yield sub
        else:
            yield item
