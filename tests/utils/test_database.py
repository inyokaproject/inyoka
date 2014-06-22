#-*- coding: utf-8 -*-
"""
    tests.utils.test_database
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2011-2014 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import datetime

from django.test import TestCase

from .models import JSONEntry
from inyoka.portal.user import User
from inyoka.utils.database import update_model


class TestDatabase(TestCase):

    def test_database_update(self):
        user = User.objects.create_user('test123', 't@bla.xy', 'test123')
        update_model(user, email='another.bla')
        self.assertEqual(user.email, 'another.bla')
        self.assertTrue(User.objects.filter(email='another.bla').exists())

        update_model(user, settings={'test': 123})
        self.assertEqual(user.settings, {'test': 123})
        # Refresh the user from the db (don't use .get to ignore the cache)
        user = User.objects.filter(pk=user.pk)[0]
        self.assertEqual(user.settings, {'test': 123})


class A(object):
    def f(self, x):
        return x * x


class JSONTest(TestCase):
    def setUp(self):
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
        entry = self.manager.create(f={'k': u'åäö'})
        entry = self.manager.get(pk=entry.pk)
        self.assertEqual(entry.f, {'k': u'åäö'})
