# -*- coding: utf-8 -*-
"""
    tests.utils.test_user
    ~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2007-2016 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import unittest
from hashlib import sha1

from django.conf import settings

from inyoka.portal.user import User, Group
from inyoka.utils.user import gen_activation_key


class TestUtilsUser(unittest.TestCase):
    def setUp(self):
        Group.objects.create_system_groups()
        User.objects.create_system_users()
        self.user = User.objects.register_user('testing', 'example@example.com',
                                               'pwd', False)

    def test_gen_activation_key(self):
        # We need to fakly generate the hash here because we're using the
        # user.id and MySQL does not handle primary keys well during
        # unittests runs so that we get the wrong id here everytime.
        # This way we cannot use a pregenerated key :(
        hash = sha1(('%d%s%s%s' % (self.user.id, self.user.username,
                                   settings.SECRET_KEY, self.user.email)))
        hash = hash.digest()[:9].encode('base64') \
                   .strip('\n=').replace('/', '_').replace('+', '-')
        self.assertEqual(gen_activation_key(self.user), hash)
