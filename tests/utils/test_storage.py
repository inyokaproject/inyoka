# -*- coding: utf-8 -*-
"""
    tests.utils.test_storage
    ~~~~~~~~~~~~~~~~~~~~~~~~

    This module tests the the storage object that uses a combination of cache
    and database storing.

    :copyright: (c) 2007-2022 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import time

from django.core.cache import caches

from inyoka.portal.models import Storage
from inyoka.utils.local import local
from inyoka.utils.storage import storage
from inyoka.utils.test import TestCase


class TestStorage(TestCase):

    def setUp(self):
        super(TestStorage, self).setUp()
        local.cache = {}
        self.cache = caches['default']

    def test_set(self):
        def _compare(key, value):
            Storage.objects.get(key=key)
            self.assertEqual(value, self.cache.get('storage/' + key))
            self.assertEqual(value, storage[key])
        storage['xyz'] = 'test'
        _compare('xyz', 'test')

        storage['test'] = 'foo'
        storage['test'] = 'bar'
        _compare('test', 'bar')

        storage.set('test', 'boo', 1)
        _compare('test', 'boo')

        time.sleep(2)
        self.assertTrue(self.cache.get('storage/test') is None)

        storage['foo'] = 'bar'
        storage['boo'] = 'far'
        self.assertEqual(storage.get_many(['foo', 'boo', 'nonexisting']), {
            'foo': 'bar',
            'boo': 'far',
        })
