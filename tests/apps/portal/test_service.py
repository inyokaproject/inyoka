"""
tests.apps.portal.test_service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test service-endpoints of the portal.

:copyright: (c) 2007-2026 by the Inyoka Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from django.contrib.auth.models import Group
from django.test import RequestFactory
from freezegun import freeze_time

from inyoka.portal.services import (
    autocompletable,
)
from inyoka.portal.user import User
from inyoka.utils.test import TestCase


class TestPortalServices(TestCase):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()

        self.alice = User.objects.register_user(
            'alice', 'alice@example.test', 'secret', False
        )
        self.alina = User.objects.register_user(
            'alina', 'alina@example.test', 'secret', False
        )
        self.albert = User.objects.register_user(
            'albert', 'albert@example.test', 'secret', False
        )
        self.bob = User.objects.register_user(
            'bob', 'bob@example.test', 'secret', False
        )
        self.inactive = User.objects.register_user(
            'aliba', 'aliba@example.test', 'secret', True
        )
        self.inactive.status = User.STATUS_INACTIVE
        self.inactive.save()

        Group.objects.create(name='admins')
        Group.objects.create(name='alpha')
        Group.objects.create(name='alpine')

    def test_autocompletable(self):
        self.assertFalse(autocompletable(''))
        self.assertFalse(autocompletable('aa'))

        self.assertTrue(autocompletable('aaa'))
        self.assertTrue(autocompletable('username'))

    def test_get_user_autocompletion_short_query(self):
        response = self.client.get('/?__service__=portal.get_user_autocompletion&q=al')

        self.assertContains(response, 'null')

    def test_get_user_autocompletion(self):
        response = self.client.get('/?__service__=portal.get_user_autocompletion&q=ali')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), '["alice", "alina"]')

    def test_get_group_autocompletion_short_query(self):
        response = self.client.get('/?__service__=portal.get_group_autocompletion&q=al')

        self.assertContains(response, 'null')

    def test_get_group_autocompletion(self):
        response = self.client.get(
            '/?__service__=portal.get_group_autocompletion&q=alp'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), '["alpha", "alpine"]')

    @freeze_time('2023-12-09T23:55:04Z')
    def test_hide_global_message_for_authenticated_user(self):
        self.client.force_login(user=self.alice)
        response = self.client.get('/?__service__=portal.hide_global_message')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), 'true')
        self.alice.refresh_from_db()
        self.assertEqual(self.alice.settings['global_message_hidden'], 1702166104.0)

    def test_hide_global_message_for_anonymous_user(self):
        response = self.client.get('/?__service__=portal.hide_global_message')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), 'false')
