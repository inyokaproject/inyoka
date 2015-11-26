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
from django.core.cache import cache
from django.utils.translation import ugettext as _
from django_redis.cache import RedisCache as _RedisCache


class QueryCounter(object):
    """
    Calls .count() for a query and saves this value into redis.
    """

    def __init__(self, cache_key, query, use_task=False, timeout=None):
        """
        task has to be a celery task that generates the counter.

        All the task has to do is call this QueryCounters build_cache method.
        """
        self.cache_key = cache_key
        self.query = query
        self.use_task = use_task
        self.timeout = timeout or settings.COUNTER_CACHE_TIMEOUT

    def __unicode__(self):
        """
        Returns the value or the unicode string "counting..."
        """
        return unicode(self.value(default=_(u"counting...")))

    def __call__(self, default=None):
        return self.value(default=default)

    def db_count(self, into_cache=False):
        """
        Executes the query with .count() and returns the value.

        Saves the value into the cache in into_cache is True.
        """
        value = self.query.count()
        cache.set(self.cache_key, value, timeout=self.timeout)
        return value

    def value(self, default=None):
        """
        Returns the value from the cache.

        If the value is not in the cache and this object was initialized with
        task, then the task is executed with celery and default is returned.

        In other case cache.get_or_set() is used to create the value. This
        blocks all requests until the value is created, so this should only be
        done for fast queries.
        """
        try:
            return self._value
        except AttributeError:
            # The value was not cached yet.
            pass
        if not self.use_task:
            count = cache.get_or_set(self.cache_key, self.db_count, self.timeout)
        else:
            count = cache.get(self.cache_key)
            if count is None:
                from inyoka.portal.tasks import query_counter_task
                # Build a queryset like query.count()
                count_query = self.query.query.clone()
                count_query.add_count_column()
                count_query.default_cols = False

                query_counter_task.delay(self.cache_key, str(count_query))
                count = None
        self._value = count
        # If count is None, then we cache None and not the default value
        if count is None:
            return default
        return count

    def incr(self, count=1):
        """
        Adds count to the counter.

        Does nothing if the counter is not in the cache.
        """
        try:
            cache.incr(self.cache_key, count)
        except ValueError:
            pass

    def decr(self, count=1):
        """
        Decreace the counter by count.

        Does nothing if the counter is not in the cache.
        """
        try:
            cache.decr(self.cache_key, count)
        except ValueError:
            pass


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
