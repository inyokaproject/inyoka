# -*- coding: utf-8 -*-
from django.conf import settings
from django.test import TestCase

from inyoka.portal.user import User, ProfileCategory, ProfileField, \
     ProfileData, PERMISSION_NAMES
from inyoka.utils.test import InyokaClient


class TestViews(TestCase):

    client_class = InyokaClient

    def setUp(self):
        self.client.defaults['HTTP_HOST'] = 'portal.{0:s}'.format(settings.BASE_DOMAIN_NAME)
        self.user = User.objects.register_user('foobar', 'foobar@inyoka.local',
                                               'password', False)
        self.admin = User.objects.register_user('admin', 'admin@inyoka.local',
                                                'password', False)
        self.admin._permissions = sum(PERMISSION_NAMES.keys())
        self.admin.save()

    def test_profile(self):
        # add some profile fields to the user
        categories = []
        categories.append(ProfileCategory(title='One'))
        categories.append(ProfileCategory(title='Two'))
        categories[0].save()
        categories[1].save()
        fields = []
        fields.append(ProfileField(title='A', category=categories[0]))
        fields.append(ProfileField(title='B', category=categories[1]))
        fields.append(ProfileField(title='C', category=categories[1]))
        fields.append(ProfileField(title='D', category=categories[1]))
        fields.append(ProfileField(title='E'))
        for field in fields:
            field.save()
        ProfileData(user=self.user, profile_field=fields[1], data='U').save()
        ProfileData(user=self.user, profile_field=fields[1], data='V').save()
        ProfileData(user=self.user, profile_field=fields[2], data='W').save()
        ProfileData(user=self.user, profile_field=fields[4], data='X').save()
        ProfileData(user=self.user, profile_field=fields[4], data='Y').save()

        # test permissions
        response = self.client.get('/user/invalid/')
        self.assertEqual(response.status_code, 302)
        response = self.client.get('/user/foobar/')
        self.assertEqual(response.status_code, 302)
        self.client.login(username='foobar', password='password')
        response = self.client.get('/user/invalid/')
        self.assertEqual(response.status_code, 404)
        response = self.client.get('/user/foobar/')
        self.assertEqual(response.status_code, 200)

        categories = response.context[0]['categories']
        self.assertEqual(len(categories), 1)
        category = categories[0]
        data = category['data']
        self.assertEqual(category['title'], 'Two')
        self.assertEqual(len(data), 3)
        self.assertEqual(data[0]['title'], 'B')
        self.assertEqual(data[1]['title'], 'B')
        self.assertEqual(data[2]['title'], 'C')
        self.assertEqual(data[0]['data'], 'U')
        self.assertEqual(data[1]['data'], 'V')
        self.assertEqual(data[2]['data'], 'W')
        data = response.context[0]['data_uncategorized']
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['title'], 'E')
        self.assertEqual(data[1]['title'], 'E')
        self.assertEqual(data[0]['data'], 'X')
        self.assertEqual(data[1]['data'], 'Y')
