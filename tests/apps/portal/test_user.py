#-*- coding: utf-8 -*-
"""
    tests.apps.portal.test_user
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test some user model functions

    :copyright: (c) 2007-2014 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import unittest
from datetime import datetime, timedelta

from django.test import TestCase

from inyoka.portal.user import User, Group, deactivate_user, reactivate_user


class TestUserModel(TestCase):
    def setUp(self):
        self.user = User.objects.register_user('testing', 'example@example.com',
                                               'pwd', False)

    def test_deactivation(self):
        """Test if the user status is correctly changed after deactivating a
        user.
        """
        deactivate_user(self.user)
        self.user = User.objects.get(pk=self.user.id)
        self.assertEqual(self.user.status, 3)


class TestGroupModel(TestCase):
    def setUp(self):
        self.group = Group.objects.create(name='testing', is_public=True)

    def test_icon(self):
        # TODO? What should be tested here?
        self.assertEqual(self.group.icon_url, None)
