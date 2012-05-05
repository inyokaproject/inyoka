# -*- coding: utf-8 -*-
from django.conf import settings
from django.test import TestCase

from inyoka.portal.user import User, PERMISSION_NAMES
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
        permissions = sum(PERMISSION_NAMES.keys())
        self.admin.save()

    def test_profile(self):
        response = self.client.get('/user/invalid/')
        self.assertEqual(response.status_code, 302)
        response = self.client.get('/user/foobar/')
        self.assertEqual(response.status_code, 302)
        self.client.login(username='foobar', password='password')
        response = self.client.get('/user/invalid/')
        self.assertEqual(response.status_code, 404)
        response = self.client.get('/user/foobar/')
        self.assertEqual(response.status_code, 200)
