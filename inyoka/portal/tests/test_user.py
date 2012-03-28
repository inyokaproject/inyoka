#-*- coding: utf-8 -*-
"""
    inyoka.portal.tests.test_user
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2007-2012 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import unittest
from datetime import datetime, timedelta
from django.test import TestCase
from inyoka.portal.user import User, Group, ProfileData, ProfileField, \
     ProfileCategory, reactivate_user, deactivate_user


class TestUserModel(TestCase):
    def setUp(self):
        self.user = User.objects.register_user('testing', 'example@example.com',
                                               'pwd', False)
        self.profile_category = ProfileCategory(title='Bar')
        self.profile_field = ProfileField(title='Test',
                                          category=self.profile_category)
        self.profile_field.save()

    def test_reactivation(self):
        result = reactivate_user(self.user.id, '', '', datetime.utcnow())
        self.assertIn('failed', result)
        result = reactivate_user(self.user.id, '', '', datetime.utcnow() - timedelta(days=34))
        self.assertIn('failed', result)
        self.user.status = 3
        self.user.save()
        result = reactivate_user(self.user.id, 'example_new@example.com',\
                                 1, datetime.now())
        self.assertIn('success', result)
        self.user = User.objects.get(pk=self.user.id)
        self.assertEqual(self.user.status, 1)

    def test_deactivation(self):
        deactivate_user(self.user)
        self.user = User.objects.get(pk=self.user.id)
        self.assertEqual(self.user.status, 3)

    def test_profile_data(self):
        field_data = ProfileData(user=self.user,
                                 profile_field=self.profile_field,
                                 data='Hello')
        field_data.save()
        data = ProfileData.objects.get(user=self.user)
        self.assertEqual(data, self.user.profile_data.get(data='Hello'))


class TestGroupModel(unittest.TestCase):
    def setUp(self):
        self.group = Group.objects.create(name='testing', is_public=True)

    def test_icon(self):
        self.assertEqual(self.group.icon_url, None)

    def tearDown(self):
        self.group.delete()
