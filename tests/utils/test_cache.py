# -*- coding: utf-8 -*-
"""
    tests.utils.test_cache
    ~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2007-2022 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from mock import DEFAULT, MagicMock, patch

from inyoka.utils.cache import RedisCache
from inyoka.utils.test import TestCase


class TestRedisCache(TestCase):
    """
    Tests the redis content cache.
    """

    @patch.multiple(
        RedisCache,
        __init__=lambda self: None,
        client=DEFAULT,
        make_key=lambda self, key: key,
    )
    def test_value_in_cache(self, client):
        """
        Simulate case in which there is a value in the cache.
        """
        client.decode.side_effect = lambda x: 'decoded %s' % x
        redis = MagicMock(name='redis')
        redis.get.return_value = 'cached value'  # Value in the cache
        client.get_client.return_value = redis
        redis_cache = RedisCache()

        value = redis_cache.get_or_set('test', lambda: 'test value', 30)

        self.assertEqual(
            value,
            'decoded cached value',
            "The value from the cache should be decoded and returned.",
        )
        self.assertFalse(
            redis.set.called,
            "redis.set() should not be called.",
        )
        self.assertEqual(
            redis.get.call_count,
            1,
            "redis.get() should only be called once.",
        )

    @patch.multiple(
        RedisCache,
        __init__=lambda self: None,
        client=DEFAULT,
        make_key=lambda self, key: key,
    )
    def test_value_not_in_cache(self, client):
        """
        Test case, where the value is not the redis cache.
        """
        client.decode.side_effect = lambda x: 'decoded %s' % x
        client.encode.side_effect = lambda x: 'encoded %s' % x
        redis = MagicMock(name='redis')
        redis.get.return_value = None  # No Value in the cache
        client.get_client.return_value = redis
        redis_cache = RedisCache()

        value = redis_cache.get_or_set('test', lambda: 'test value', 30)

        self.assertEqual(
            value,
            'decoded encoded test value',
            "The value from the callback argument should be encoded, decoded and returned.",
        )
        self.assertEqual(
            redis.set.call_count,
            2,
            "redis.set() should be called two times.",
        )
        self.assertEqual(
            redis.get.call_count,
            1,
            "redis.get() should only be called once.",
        )

    @patch('inyoka.utils.cache.sleep')
    @patch.multiple(
        RedisCache,
        __init__=lambda self: None,
        client=DEFAULT,
        make_key=lambda self, key: key,
    )
    def test_value_not_in_cache_two_parallel_clients(self, sleep, client):
        """
        Test case where there is no value in the cache and two clients access
        it at the same time. The test call simulates the second call.
        """
        client.decode.side_effect = lambda x: 'decoded %s' % x
        client.encode.side_effect = lambda x: 'encoded %s' % x
        redis = MagicMock(name='redis')
        redis.get.side_effect = (None, None, 'cached value')  # Value in cache after the third call
        redis.set.return_value = False  # The set call fails (value already in the cache)
        client.get_client.return_value = redis
        redis_cache = RedisCache()

        value = redis_cache.get_or_set('test', lambda: 'test value', 30)

        self.assertEqual(
            value,
            'decoded cached value',
            "The value from the callback argument should be decoded and returned.",
        )
        self.assertEqual(
            redis.set.call_count,
            2,
            "redis.set() should be called two times.",
        )
        self.assertEqual(
            redis.get.call_count,
            3,
            "redis.get() should be called three times.",
        )
        self.assertEqual(
            sleep.call_count,
            2,
            "sleep() should be called two times.",
        )
