#-*- coding: utf-8 -*-
"""
    inyoka.utils.tests.test_cache
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2007-2012 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from django.test import TestCase

from inyoka.utils.cache import get_cache
from inyoka.utils.local import local


class TestCache(TestCase):

    def setUp(self):
        local.cache = {}
        self.real = {}
        self.cache = get_cache('default')
        self.request_cache = get_cache('request')
        self.request_cache.request_cache = self.real

    def test_seperate(self):
        def _compare(key, value, exists=True):
            self.assertEqual(value, self.cache.get(key))
            self.assertEqual(value, self.request_cache.get(key))
            self.assertEqual(key in self.request_cache.request_cache, exists)

        self.request_cache.set('test', 'foo')
        self.request_cache.set('test', 'bar')
        self.request_cache.set('bar', 'foo')
        _compare('test', 'bar')
        _compare('blah', None, False)
        _compare('bar', 'foo')


    def test_many(self):
        def _compare_many(keys, value):
            self.assertEqual(value, self.cache.get_many(keys))
            self.assertEqual(value, self.request_cache.get_many(keys))

        def _compare(key, value, exists=True):
            self.assertEqual(value, self.cache.get(key))
            self.assertEqual(value, self.request_cache.get(key))
            self.assertEqual(key in self.request_cache.request_cache, exists)

        self.request_cache.set_many({
            'test': 'bar',
            'bar': 'foo'
        })

        _compare_many(('test', 'bar', 'blah'), {'test': 'bar', 'bar': 'foo'})
        _compare('test', 'bar')
        _compare('bar', 'foo')
        _compare('blah', None, False)

    def test_delete(self):
        self.request_cache.set('foo', 'bar')
        self.assertEqual(self.request_cache.get('foo'), 'bar')
        self.request_cache.delete('foo')
        self.assertEqual(self.request_cache.get('foo'), None)
