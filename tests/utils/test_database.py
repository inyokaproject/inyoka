# -*- coding: utf-8 -*-
"""
    tests.utils.test_database
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2011-2023 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import datetime

from inyoka.utils.test import TestCase

from .models import JSONEntry


class A(object):
    def f(self, x):
        return x * x


class JSONTest(TestCase):
    def setUp(self):
        super(JSONTest, self).setUp()
        self.model = JSONEntry
        self.manager = self.model.objects

    def test_create(self):
        entry = self.manager.create(pk=100, f={'k': 1})
        self.assertEqual(entry.f, {'k': 1})

    def test_assign(self):
        entry = self.manager.create(f={'k': 2})
        entry.f['k'] = {'j': 1}
        entry.save()
        self.assertEqual(entry.f, {'k': {'j': 1}})

    def test_NULL(self):
        entry = self.manager.create(f=None)
        entry = self.manager.get(pk=entry.pk)
        self.assertEqual(entry.f, None)

    def test_empty(self):
        entry = self.manager.create(f='')
        entry = self.manager.get(pk=entry.pk)
        self.assertEqual(entry.f, '')

    def test_empty_dict(self):
        entry = self.manager.create(f={})
        entry = self.manager.get(pk=entry.pk)
        self.assertEqual(entry.f, {})

    def test_date(self):
        d = datetime.date.today()
        entry = self.manager.create(f={'d': d})
        self.assertEqual(entry.f, {'d': d})

    def test_unicode(self):
        entry = self.manager.create(f={'k': 'åäö'})
        entry = self.manager.get(pk=entry.pk)
        self.assertEqual(entry.f, {'k': 'åäö'})
