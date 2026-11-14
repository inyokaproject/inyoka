"""
tests.utils.test_notification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Tests for the Inyoka notification utilities.

:copyright: (c) 2011-2026 by the Inyoka Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from unittest.mock import MagicMock, patch

from django.contrib.contenttypes.models import ContentType
from django.core import mail

from inyoka.portal.models import Subscription
from inyoka.portal.user import User
from inyoka.utils.notification import (
    notify_about_subscription,
    queue_notifications,
    send_notification,
)
from inyoka.utils.test import TestCase


class TestNotification(TestCase):
    def setUp(self):
        super().setUp()
        self.admin = User.objects.register_user(
            'admin', 'admin@inyoka.test', 'admin', False
        )
        self.admin.is_superuser = True
        self.admin.save()

        self.admin.settings['notify'] = ['mail']
        self.admin.settings['notifications'] = ('topic_split',)
        self.admin.save()

    def test_send_notification(self):
        args = {'title': 'title', 'username': self.admin.username, 'note': 'note'}
        send_notification(
            self.admin, 'suggestion_rejected', 'Deleted suggestion', args=args
        )

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject, 'inyokaproject.org: Deleted suggestion'
        )
        self.assertNotIn('{', mail.outbox[0].body)

    def _create_user(self, username: str):
        email = f'{username}@inyoka.test'
        user = User.objects.register_user(username, email, 'secret', False)

        user.settings['notify'] = ['mail']
        user.save(update_fields=['settings'])

        return user

    def _make_subscription(self, user, notified=False):
        content_type = ContentType.objects.get_for_model(User)
        return Subscription.objects.create(
            user=user,
            content_type=content_type,
            object_id=user.id,
            notified=notified,
        )

    def test_send_notification_skips_deleted_users(self):
        deleted_user = self._create_user('deleted-user')
        deleted_user.status = User.STATUS_DELETED
        deleted_user.save()

        send_notification(
            deleted_user,
            'suggestion_rejected',
            'Deleted suggestion',
            {'username': deleted_user.username},
        )
        self.assertEqual(len(mail.outbox), 0)

    def test_send_notification__requires_subject(self):
        with self.assertRaises(AssertionError):
            send_notification(
                self.admin,
                'suggestion_rejected',
                None,
                {'username': self.admin.username},
            )

    def test_send_notification_ignores_non_mail_methods(self):
        self.admin.settings['notify'] = ['sms']
        self.admin.save()

        send_notification(
            self.admin,
            'suggestion_rejected',
            'Deleted suggestion',
            {'username': self.admin.username},
        )

        self.assertEqual(len(mail.outbox), 0)

    def test_notify_about_subscription_no_access_perms(self):
        subscription = self._make_subscription(self.admin)

        with patch('inyoka.utils.notification.send_notification') as send_mock:
            subscription.can_read = MagicMock(return_value=False)
            notify_about_subscription(
                subscription,
                'topic_split',
                'Subject',
                {'forum_id': 42},
            )
            send_mock.assert_not_called()

    def test_notify___settings_do_not_match(self):
        subscription = self._make_subscription(self.admin)

        with patch('inyoka.utils.notification.send_notification') as send_mock:
            subscription.can_read = MagicMock(return_value=True)
            self.admin.settings['notifications'] = ('other_topic',)
            self.admin.save()

            notify_about_subscription(
                subscription,
                'topic_split',
                'Subject',
                {'forum_id': 42},
            )
            send_mock.assert_not_called()

    def test_notify__setting_does_match(self):
        subscription = self._make_subscription(self.admin)

        with patch('inyoka.utils.notification.send_notification') as send_mock:
            self.admin.settings['notifications'] = ('topic_split',)
            self.admin.save()

            notify_about_subscription(
                subscription,
                'topic_split',
                'Subject',
                {'forum_id': 42},
            )
            send_mock.assert_called_once_with(
                self.admin,
                'topic_split',
                'Subject',
                {'forum_id': 42},
            )

    def test_queue_notifications_requires_filter(self):
        with self.assertRaises(AssertionError):
            queue_notifications(
                request_user_id=self.admin.id,
                template='topic_split',
                subject='Subject',
                args={'forum_id': 1},
                include_notified=False,
                exclude_current_user=True,
                filter=None,
            )

    def test_queue_notifications_requires_args(self):
        with self.assertRaises(AssertionError):
            queue_notifications(
                request_user_id=self.admin.id,
                template='topic_split',
                subject='Subject',
                args=None,
                include_notified=False,
                exclude_current_user=True,
                filter={'user__in': [self.admin]},
            )

    @patch('inyoka.utils.notification.notify_about_subscription')
    @patch('inyoka.utils.notification.subtask')
    def test_queue_notifications_updates_notified_and_callback(
        self,
        subtask_mock,
        notify_about_subscription_mock,
    ):
        user_a = self._create_user('user-a')
        user_b = self._create_user('user-b')
        user_c = self._create_user('user-c')

        sub_a = self._make_subscription(user_a)
        self._make_subscription(user_b)
        sub_c = self._make_subscription(user_c)

        result = queue_notifications(
            request_user_id=user_b.id,
            template='topic_split',
            subject='Subject',
            args={'forum_id': 99},
            exclude_current_user=True,
            filter={'user__in': [user_a, user_b, user_c], 'notified': False},
            exclude={'user_id__in': [user_c.id]},
            callback='fake_callback',
        )

        self.assertSetEqual(set(result), {user_a.id, user_c.id})
        self.assertEqual(notify_about_subscription_mock.call_count, 1)

        self.assertTrue(Subscription.objects.get(pk=sub_a.pk).notified)
        self.assertFalse(Subscription.objects.get(pk=sub_c.pk).notified)

        subtask_mock.assert_called_once()
        notified_users = subtask_mock.return_value.delay.call_args.args[0]
        self.assertSetEqual(set(notified_users), {user_a.id, user_c.id})

    @patch('inyoka.utils.notification.notify_about_subscription')
    @patch('inyoka.utils.notification.subtask')
    def test_queue_notifications_can_include_already_notified_records(
        self,
        subtask_mock,
        notify_about_subscription_mock,
    ):
        user = self._create_user('already-seen')
        subscription = self._make_subscription(user, notified=True)

        result = queue_notifications(
            request_user_id=self.admin.id,
            template='topic_split',
            subject='Subject',
            args={'forum_id': 99},
            include_notified=True,
            exclude_current_user=False,
            filter={'user': user},
            exclude=None,
            callback=lambda: 'fake_callback',
        )

        self.assertEqual(result, [user.id])
        self.assertTrue(Subscription.objects.get(pk=subscription.pk).notified)

        notify_about_subscription_mock.assert_called_once()
        subtask_mock.assert_called_once()

        notified_users = subtask_mock.return_value.delay.call_args.args[0]
        self.assertEqual(notified_users, [user.id])
