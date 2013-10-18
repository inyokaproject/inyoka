# -*- coding: utf-8 -*-
"""
    inyoka.utils.cache
    ~~~~~~~~~~~~~~~~~~

    The caching infrastructure of Inyoka.

    On top of the django cache client that speaks directly to either memcached
    or caches in-memory we have a :class:`RequestCache` that caches
    memcached-commands in a thread-local dictionary.  This saves a lot of
    memcached-commands in some szenarios.

    :copyright: (c) 2007-2013 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from django.core.cache import cache, get_cache
from django.core.cache.backends.base import BaseCache

from inyoka.utils.local import local_has_key, _request_cache


class RequestCache(BaseCache):
    """A helper cache to cache the requested stuff in a threadlocal."""
    def __init__(self, _, params):
        BaseCache.__init__(self, params)
        self.real_cache = cache
        self.request_cache = _request_cache

    def get(self, key, default=None, version=None):
        if local_has_key('cache'):
            try:
                return self.request_cache[key]
            except KeyError:
                val = self.real_cache.get(key, default, version)
                if val is not None:
                    self.request_cache[key] = val

                return val
        else:
            return self.real_cache.get(key, default, version)

    def get_many(self, keys, version=None):
        if not local_has_key('cache'):
            return self.real_cache.get_many(keys, version)
        key_mapping = {}

        # fetch keys that are not yet in the thread local cache
        keys_to_fetch = set(keys).difference(set(self.request_cache.keys()))
        key_mapping.update(self.real_cache.get_many(keys_to_fetch, version))

        # pull in remaining keys from thread local cache.
        missing = set(keys).difference(keys_to_fetch)
        key_mapping.update({key: self.request_cache[key] for key in missing})

        # Update the request cache
        self.request_cache.update(key_mapping)
        return key_mapping

    def set(self, key, value, timeout=None, version=None):
        if local_has_key('cache'):
            self.request_cache[key] = value
        return self.real_cache.set(key, value, timeout, version)

    def set_many(self, data, timeout=None, version=None):
        if local_has_key('cache'):
            self.request_cache.update(data)
        return self.real_cache.set_many(data, timeout, version)

    def delete(self, key, version=None):
        if local_has_key('cache') and key in self.request_cache:
            self.request_cache.pop(key)
        self.real_cache.delete(key, version)

    def clear(self):
        if local_has_key('cache'):
            self.request_cache.clear()
        self.real_cache.clear()


request_cache = get_cache('request')
