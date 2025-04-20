"""
    tests.utils.test_user
    ~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2007-2025 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.conf import settings
from django.test.utils import override_settings
from freezegun import freeze_time

from inyoka.portal.user import User
from inyoka.utils.test import TestCase
from inyoka.utils.user import gen_activation_key, check_activation_key


class TestUtilsUser(TestCase):

    @freeze_time('2025-01-20 13:13:37')
    @override_settings(SECRET_KEY='FOOBAR_SECRETE_39q4utfhaer')
    def test_gen_activation_key(self):
        u = User.objects.create(id=133337, username='testing', email='example@example.test')

        self.assertEqual(
            gen_activation_key(u),
            'eyJ1c2VyX2lkIjoxMzMzMzcsInVzZXJuYW1lIjoidGVzdGluZyJ9:1tZraz:6jRPSJsiYTZKpBefCoQ4OO8-tBca6PFLFyGldrftAfM'
        )

    def test_check_activation_key(self):
        u = User.objects.create(username='testing',
                                email='example@example.test')

        key = gen_activation_key(u)
        self.assertTrue(check_activation_key(u, key))

    def test_check_activation_key__expired(self):
        u = User.objects.create(username='testing',
                                email='example@example.test')

        with freeze_time('2025-01-20 13:13:37'):
            key = gen_activation_key(u)

        with freeze_time('2026-01-01'): # a year later, the key should be invalid
            self.assertFalse(check_activation_key(u, key))
