"""
    tests.utils.test_notification
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tests for the Inyoka notification utilities.

    :copyright: (c) 2011-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.core import mail

from inyoka.portal.user import User
from inyoka.utils.notification import send_notification
from inyoka.utils.test import TestCase


class TestNotification(TestCase):

    def setUp(self):
        super().setUp()
        self.admin = User.objects.register_user('admin', 'admin@inyoka.test', 'admin', False)
        self.admin.is_superuser = True
        self.admin.save()

    def test_send_notification(self):
        args = {'title': 'title',
                'username': self.admin.username,
                'note': 'note'}
        send_notification(self.admin, 'suggestion_rejected', 'Deleted suggestion', args=args)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "inyokaproject.org: Deleted suggestion")
        self.assertNotIn('{', mail.outbox[0].body)
