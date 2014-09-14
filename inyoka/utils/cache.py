# -*- coding: utf-8 -*-
"""
    inyoka.utils.cache
    ~~~~~~~~~~~~~~~~~~

    The caching infrastructure of Inyoka.

    On top of the django cache client that speaks directly to either memcached
    or caches in-memory we have a :class:`RequestCache` that caches
    memcached-commands in a thread-local dictionary.  This saves a lot of
    memcached-commands in some szenarios.

    :copyright: (c) 2007-2014 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import hashlib

from django.conf import settings
from django.core.cache import cache, get_cache
from django.core.cache.backends.base import BaseCache
from django.utils.encoding import force_bytes

from inyoka.utils.local import local_has_key, _request_cache

_MAX_KEY_LENGTH = 250


def _shorten_key(key):
    # Some caching systems like memcached dont like cache keys > 250 chars.
    return 'md5:%s' % hashlib.md5(force_bytes(key)).hexdigest()


class RequestCache(BaseCache):
    """A helper cache to cache the requested stuff in a threadlocal."""
    def __init__(self, _, params):
        BaseCache.__init__(self, params)
        self.real_cache = cache
        self.request_cache = _request_cache

    def get(self, key, default=None, version=None):
        if len(key) > _MAX_KEY_LENGTH:
            key = _shorten_key(key)
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
        long_key_mapping = {}
        new_keys = []
        for key in keys:
            if len(key) > _MAX_KEY_LENGTH:
                hash = _shorten_key(key)
                long_key_mapping[hash] = key
                new_keys.append(hash)
            else:
                new_keys.append(key)
        if not local_has_key('cache'):
            return self.real_cache.get_many(new_keys, version)
        key_mapping = {}

        # fetch keys that are not yet in the thread local cache
        keys_to_fetch = set(new_keys).difference(set(self.request_cache.keys()))
        key_mapping.update(self.real_cache.get_many(keys_to_fetch, version))

        # pull in remaining keys from thread local cache.
        missing = set(new_keys).difference(keys_to_fetch)
        key_mapping.update({key: self.request_cache[key] for key in missing})

        # Update the request cache
        self.request_cache.update(key_mapping)
        for h, k in long_key_mapping.iteritems():
            key_mapping[k] = key_mapping.pop(h)
        return key_mapping

    def set(self, key, value, timeout=None, version=None):
        if len(key) > _MAX_KEY_LENGTH:
            key = _shorten_key(key)
        if local_has_key('cache'):
            self.request_cache[key] = value
        self.real_cache.set(key, value, timeout, version)

    def set_many(self, data, timeout=None, version=None):
        new_data = {}
        for k in data:
            if len(k) > _MAX_KEY_LENGTH:
                new_data[_shorten_key(k)] = data[k]
            else:
                new_data[k] = data[k]
        if local_has_key('cache'):
            self.request_cache.update(new_data)
        self.real_cache.set_many(new_data, timeout, version)

    def delete(self, key, version=None):
        if len(key) > _MAX_KEY_LENGTH:
            key = _shorten_key(key)
        if local_has_key('cache') and key in self.request_cache:
            self.request_cache.pop(key)
        self.real_cache.delete(key, version)

    def clear(self):
        if local_has_key('cache'):
            self.request_cache.clear()
        self.real_cache.clear()

if 'debug_toolbar' in settings.INSTALLED_APPS:
    from debug_toolbar.panels.cache import get_cache_debug as get_cache
request_cache = get_cache('request')
