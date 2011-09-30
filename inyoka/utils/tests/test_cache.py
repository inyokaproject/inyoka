#-*- coding: utf-8 -*-
"""
    inyoka.utils.tests.test_cache
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import time

from django.test import TestCase
from django.core.cache import cache

from inyoka.utils.cache import request_cache, cache
from inyoka.utils.local import local, _request_cache


class TestStorage(TestCase):

    def setUp(self):
        local.cache = {}

    def test_set(self):
        def _compare(key, value, exists=True):
            self.assertEqual(value, cache.get(key))
            self.assertEqual(value, request_cache.get(key))
            self.assertEqual(key in request_cache.request_cache, exists)

        def _compare_many(keys, value):
            self.assertEqual(value, cache.get_many(keys))
            self.assertEqual(value, request_cache.get_many(keys))

        request_cache.set('test', 'foo')
        request_cache.set('test', 'bar')
        request_cache.set('bar', 'foo')
        _compare('test', 'bar')
        _compare('blah', None, False)
        _compare('bar', 'foo')
        _compare_many(('test', 'bar', 'blah'), {'test': 'bar', 'bar': 'foo'})
        _compare('test', 'bar')
        _compare('bar', 'foo')
        _compare('blah', None, False)
