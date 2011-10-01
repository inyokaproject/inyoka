#-*- coding: utf-8 -*-
"""
    inyoka.utils.tests.test_database
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from django.test import TestCase

from inyoka.portal.user import User
from inyoka.utils.database import update_model


class TestDatabase(TestCase):

    def test_database_update(self):
        user = User.objects.create_user('test123', 't@bla.xy', 'test123')
        update_model(user, email='another.bla')
        self.assertEqual(user.email, 'another.bla')
