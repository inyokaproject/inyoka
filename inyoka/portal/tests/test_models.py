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

    def test_delete_empty_avatar(self):
        self.user = User.objects.get(pk=self.user.id)
        # Should not raise an OSError
        self.user.delete_avatar()

    def test_profile_data(self):
        categories = [
            ProfileCategory.objects.create(title='One'),
            ProfileCategory.objects.create(title='Two'),
        ]
        users = [User.objects.register_user(str(x),
                                            '{0}@example.com'.format(x),
                                            'pwd', False) for x in range(3)]
        ProfileField.objects.create(title='A', category=categories[0])
        ProfileField.objects.create(title='B', category=categories[1])
        ProfileField.objects.create(title='C', category=categories[1])
        ProfileField.objects.create(title='D', category=categories[1])

        ProfileData.objects.create(
            user=users[0],
            profile_field=ProfileField.objects.get(title='A'),
            data='U',
        )
        ProfileData.objects.create(
            user=users[0],
            profile_field=ProfileField.objects.get(title='B'),
            data='V',
        )
        ProfileData.objects.create(
            user=users[0],
            profile_field=ProfileField.objects.get(title='B'),
            data='X',
        )
        ProfileData.objects.create(
            user=users[0],
            profile_field=ProfileField.objects.get(title='C'),
            data='W'
        )
        ProfileData.objects.create(
            user=users[2],
            profile_field=ProfileField.objects.get(title='D'),
            data='X',
        )
        ProfileData.objects.create(
            user=users[2],
            profile_field=ProfileField.objects.get(title='C'),
            data='Y'
        )
        ProfileData.objects.create(
            user=users[2],
            profile_field=ProfileField.objects.get(title='A'),
            data='Z'
        )

        # should be ordered by title of ProfileField
        data = users[0].profile_data.all()
        self.assertEqual(len(data), 4)
        self.assertEqual(data[0].data, 'U')
        self.assertEqual(data[1].data, 'V')
        self.assertEqual(data[2].data, 'X')
        self.assertEqual(data[3].data, 'W')
        self.assertEqual(data[0].profile_field.title, 'A')
        self.assertEqual(data[1].profile_field.title, 'B')
        self.assertEqual(data[2].profile_field.title, 'B')
        self.assertEqual(data[3].profile_field.title, 'C')
        self.assertEqual(data[0].profile_field.category.title, 'One')
        self.assertEqual(data[1].profile_field.category.title, 'Two')
        self.assertEqual(data[2].profile_field.category.title, 'Two')
        self.assertEqual(data[3].profile_field.category.title, 'Two')

        data = users[1].profile_data.all()
        self.assertEqual(len(data), 0)

        data = users[2].profile_data.all()
        self.assertEqual(len(data), 3)
        self.assertEqual(data[0].data, 'Z')
        self.assertEqual(data[1].data, 'Y')
        self.assertEqual(data[2].data, 'X')
        self.assertEqual(data[0].profile_field.title, 'A')
        self.assertEqual(data[1].profile_field.title, 'C')
        self.assertEqual(data[2].profile_field.title, 'D')
        self.assertEqual(data[0].profile_field.category.title, 'One')
        self.assertEqual(data[1].profile_field.category.title, 'Two')
        self.assertEqual(data[2].profile_field.category.title, 'Two')

class TestGroupModel(unittest.TestCase):
    def setUp(self):
        self.group = Group.objects.create(name='testing', is_public=True)

    def test_icon(self):
        self.assertEqual(self.group.icon_url, None)

    def tearDown(self):
        self.group.delete()
