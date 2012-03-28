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
        titles = ['One', 'Two', 'Three']
        categories = [ProfileCategory(title=title) for title in titles]
        users = [User.objects.register_user(str(x), '{0}@example.com'.format(x),
                                            'pwd', False) for x in range(3)]
        ProfileField(title='A', category=categories[0]).save()
        ProfileField(title='B', category=categories[0]).save()
        ProfileField(title='C', category=categories[0]).save()
        ProfileField(title='D', category=categories[1]).save()
        ProfileField(title='E', category=categories[2]).save()
        ProfileField(title='F', category=categories[2]).save()

        ProfileData(user=users[0],
                    profile_field=ProfileField.objects.get(title='A'),
                    data='U').save()
        ProfileData(user=users[0],
                    profile_field=ProfileField.objects.get(title='B'),
                    data='V').save()
        ProfileData(user=users[1],
                    profile_field=ProfileField.objects.get(title='E'),
                    data='X').save()
        ProfileData(user=users[2],
                    profile_field=ProfileField.objects.get(title='E'),
                    data='Y').save()
        ProfileData(user=users[2],
                    profile_field=ProfileField.objects.get(title='F'),
                    data='Y').save()

        for user in users:
            query_data = ProfileData.objects.filter(user=user) \
                                      .order_by('profile_field__title').all()
            for i, x in enumerate(user.profile_data.all()):
                self.assertEqual(query_data[i].data, x.data)
                self.assertEqual(query_data[i].profile_field, x.profile_field)

class TestGroupModel(unittest.TestCase):
    def setUp(self):
        self.group = Group.objects.create(name='testing', is_public=True)

    def test_icon(self):
        self.assertEqual(self.group.icon_url, None)

    def tearDown(self):
        self.group.delete()
