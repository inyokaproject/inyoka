# -*- coding: utf-8 -*-
"""
    inyoka.utils.cache
    ~~~~~~~~~~~~~~~~~~

    The caching infrastructure of Inyoka.

    On top of the django cache client that speaks directly to either redis
    or caches in-memory we have a :class:`RequestCache` that caches
    redis-commands in a thread-local dictionary.  This saves a lot of
    redis-commands in some szenarios.

    :copyright: (c) 2007-2015 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from time import sleep

from django.conf import settings
from django.core.cache import cache, get_cache
from django.core.cache.backends.base import BaseCache

if settings.USE_REDIS_CACHE:
    from django_redis.cache import RedisCache as _RedisCache
else:
    # Redis is an optional dependency if USE_REDIS_CACHE is False
    from django.core.cache.backends.locmem import LocMemCache as _RedisCache

from inyoka.utils.local import local_has_key, _request_cache



class RequestCache(BaseCache):
    """A helper cache to cache the requested stuff in a thread local."""

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

if 'debug_toolbar' in settings.INSTALLED_APPS:
    from debug_toolbar.panels.cache import get_cache as get_cache
request_cache = get_cache('request')


class RedisCache(_RedisCache):
    """
    Wrapper to redis cache that creates status keys for the time a value is
    created.

    Idea from https://github.com/funkybob/puppy
    """

    def get_or_set(self, key, callback, timeout=None, update_time=6):
        """
        Get a key if it exists. Creates it if other case.

        Sets a status key for the time the value is created, so other workers
        do not created the same content in the meantime.
        """
        # If redis is disabled, then we can call the callback immediately
        if not settings.USE_REDIS_CACHE:
            return callback()

        redis = self.client.get_client()

        # Status key
        key = self.make_key(key)
        state_key = key + ':status'

        # Get the value and its status
        value = redis.get(key)

        while value is None:
            # Try to gain an updating lock
            if redis.set(state_key, 'updating', ex=update_time, nx=True):
                try:
                    # TODO: log how long callback needs. If it needs more then
                    #       update_time, it should write a warning.
                    value = self.client.encode(callback())

                    # Resolve our timeout value
                    if timeout is None:
                        timeout = self.default_timeout

                    # Set the value
                    redis.set(key, value, ex=timeout)
                finally:
                    # If the key is deleted it can not be recreated before the
                    # state_key expires. So it has to be deleted
                    redis.delete(state_key)

            # Someone else is already updating it, but we don't have a value
            # to return, so we try again later
            else:
                sleep(0.1)
                value = redis.get(key)

        try:
            return self.client.decode(value)
        except:
            # If value can not be decoded, then delete it from the cache
            redis.delete(key)
            raise
