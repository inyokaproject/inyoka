# -*- coding: utf-8 -*-
"""
    inyoka.utils.pylibmc
    ~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from django.core.cache.backends.memcached import PyLibMCCache


try:
    from pylibmc import Client as PyLibMCClient
except ImportError:
    Client = type('Client', (object,), {})

MIN_COMPRESS_LEN = 150000


class CachedPyLibMCCache(PyLibMCCache):
    """A custom helper to support cache compression."""

    def set(self, key, value, timeout=0, version=None, min_compress_len=MIN_COMPRESS_LEN):
        key = self.make_key(key, version=version)
        self._cache.set(key, value, self._get_memcache_timeout(timeout), min_compress_len)

    def add(self, key, value, timeout=0, version=None, min_compress_len=MIN_COMPRESS_LEN):
        key = self.make_key(key, version=version)
        return self._cache.add(key, value, self._get_memcache_timeout(timeout), min_compress_len)

    def set_many(self, data, timeout=0, version=None, min_compress_len=MIN_COMPRESS_LEN):
        #TODO: for now compression does not work on set_multi, so we must use .set() here :(
        for key, value in data.items():
            self.set(key, value, timeout, version, min_compress_len)
