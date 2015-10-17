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

from django_redis.cache import RedisCache as _RedisCache


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
