#-*- coding: utf-8 -*-
"""
    tests.utils.test_cache
    ~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2007-2015 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.test import TestCase

from inyoka.utils.local import local
from inyoka.utils.cache import get_cache


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

    def test_short_key_exceeding_with_prefix_and_version(self):
        key = 'a' * 248
        keyhash = 'md5:6af3d61e2e3ef8e189cffbea802c7e69'

        self.request_cache.set(key, 1)
        self.assertEqual(self.request_cache.get(keyhash), 1)

        self.request_cache.delete(key)
        self.assertEqual(self.request_cache.get(keyhash), None)

        self.request_cache.set(keyhash, 2)
        self.assertEqual(self.request_cache.get(key), 2)

        self.request_cache.delete(keyhash)
        self.assertEqual(self.request_cache.get(keyhash), None)

    def test_long_key(self):
        key = 'a' * 251
        keyhash = 'md5:21f5b107cda33036590a19419afd7fb6'

        self.request_cache.set(key, 1)
        self.assertEqual(self.request_cache.get(keyhash), 1)

        self.request_cache.delete(key)
        self.assertEqual(self.request_cache.get(keyhash), None)

        self.request_cache.set(keyhash, 2)
        self.assertEqual(self.request_cache.get(key), 2)

        self.request_cache.delete(keyhash)
        self.assertEqual(self.request_cache.get(keyhash), None)

    def test_short_key_exceeding_with_prefix_and_version_many(self):
        keya = 'a' * 248
        keyahash = 'md5:6af3d61e2e3ef8e189cffbea802c7e69'
        keyb = 'b' * 248
        keybhash = 'md5:bc36adde631774af8fc8add2de9665b8'

        data = {
            'a': 'a',
            'b': 'b',
            keya: 'aaa',
            keyb: 'bbb',
        }

        datahash = {
            'a': 'a',
            'b': 'b',
            keyahash: 'aaa',
            keybhash: 'bbb',
        }

        self.request_cache.set_many(data)
        self.assertEqual(self.request_cache.get_many(data.keys()), data)

        for k in data:
            self.request_cache.delete(k)

        self.request_cache.set_many(data)
        # If we request by the hash, we cannot map to the original key
        self.assertEqual(self.request_cache.get_many(datahash.keys()), datahash)

        for k in data:
            self.request_cache.delete(k)

        self.request_cache.set_many(datahash)
        self.assertEqual(self.request_cache.get_many(data.keys()), data)

        for k in datahash:
            self.request_cache.delete(k)

        self.request_cache.set_many(datahash)
        # If we request by the hash, we cannot map to the original key
        self.assertEqual(self.request_cache.get_many(datahash.keys()), datahash)

        for k in datahash:
            self.request_cache.delete(k)

    def test_long_key_many(self):
        keya = 'a' * 251
        keyahash = 'md5:21f5b107cda33036590a19419afd7fb6'
        keyb = 'b' * 251
        keybhash = 'md5:7e1b07a8a48d8c53aa0d6144cd6b5dbb'

        data = {
            'a': 'a',
            'b': 'b',
            keya: 'aaa',
            keyb: 'bbb',
        }

        datahash = {
            'a': 'a',
            'b': 'b',
            keyahash: 'aaa',
            keybhash: 'bbb',
        }

        self.request_cache.set_many(data)
        self.assertEqual(self.request_cache.get_many(data.keys()), data)

        for k in data:
            self.request_cache.delete(k)

        self.request_cache.set_many(data)
        # If we request by the hash, we cannot map to the original key
        self.assertEqual(self.request_cache.get_many(datahash.keys()), datahash)

        for k in data:
            self.request_cache.delete(k)

        self.request_cache.set_many(datahash)
        self.assertEqual(self.request_cache.get_many(data.keys()), data)

        for k in datahash:
            self.request_cache.delete(k)

        self.request_cache.set_many(datahash)
        # If we request by the hash, we cannot map to the original key
        self.assertEqual(self.request_cache.get_many(datahash.keys()), datahash)

        for k in datahash:
            self.request_cache.delete(k)
