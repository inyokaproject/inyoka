#-*- coding: utf-8 -*-
"""
    inyoka.utils.tests.test_storage
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module tests the the storage object that uses a combination of cache
    and database storing..


    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import time

from django.test import TestCase
from django.core.cache import cache

from inyoka.portal.models import Storage
from inyoka.utils.storage import storage


class TestStorage(TestCase):
    def test_set(self):
        def _compare(key, value):
            Storage.objects.get(key=key)
            self.assertEqual(value, cache.get('storage/' + key))
            self.assertEqual(value, storage[key])
        storage['test'] = 'foo'
        storage['test'] = 'bar'
        _compare('test', 'bar')
        storage.set('test', 'boo', 1)
        _compare('test', 'boo')
        time.sleep(3)
        self.assertTrue(cache.get('storage/test') is None)
        storage['foo'] = 'bar'
        storage['boo'] = 'far'
        self.assertEqual(storage.get_many(['foo', 'boo', 'nonexisting']), {
            'foo': 'bar',
            'boo': 'far',
        })
