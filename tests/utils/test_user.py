"""
    tests.utils.test_user
    ~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2007-2023 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from hashlib import sha1

from django.conf import settings

from inyoka.portal.user import User, Group
from inyoka.utils.user import gen_activation_key
from inyoka.utils.test import TestCase


class TestUtilsUser(TestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.register_user('testing', 'example@example.com',
                                               'pwd', False)

    def test_gen_activation_key(self):
        # We need to fakly generate the hash here because we're using the
        # user.id and MySQL does not handle primary keys well during
        # unittests runs so that we get the wrong id here everytime.
        # This way we cannot use a pregenerated key :(
        to_hash = '%d%s%s%s' % (self.user.id, self.user.username, settings.SECRET_KEY, self.user.email)
        hash = sha1(to_hash.encode()).hexdigest()  # sha1 needs bytes

        self.assertEqual(gen_activation_key(self.user), hash)
