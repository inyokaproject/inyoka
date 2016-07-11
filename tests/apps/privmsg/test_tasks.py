# -*- coding: utf-8 -*-
"""
    tests.apps.privmsg.test_tasks
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test privmsg tasks.

    :copyright: (c) 2011-2016 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime, timedelta

from inyoka.portal.user import User
from inyoka.privmsg.models import MessageData, Message
from inyoka.utils.test import TestCase
from inyoka.privmsg.tasks import clean_abandoned_messages, expunge_private_messages


class TestTasks(TestCase):
    """Tests for privmsg tasks."""

    def setUp(self):
        self.author = User.objects.register_user(
            username='author',
            email='author',
            password='',
            send_mail=False,
        )

    def test_clean_abandoned_messages(self):
        """`clean_abandoned_messages()` should delete messages no longer referenced by any users."""
        MessageData.objects.create(author=self.author, subject='Test', text='Text')

        clean_abandoned_messages()

        self.assertFalse(MessageData.objects.abandoned().exists())

    def test_expunge_private_messages(self):
        """`expunge_private_messages()` should delete trashed messages after a grace period."""
        yesterday = datetime.utcnow() - timedelta(days=1)
        messagedata = MessageData.objects.create(
            author=self.author,
            subject='Test',
            text='Text',
        )
        Message.objects.create(
            messagedata=messagedata,
            recipient=self.author,
            status=Message.STATUS_TRASHED,
            trashed_date=yesterday,
        )

        expunge_private_messages()

        self.assertFalse(Message.objects.trashed().exists())

    def test_expunge_private_messages_with_newer(self):
        """`expunge_private_messages()` should not delete trashed messages before the grace period is over."""
        messagedata = MessageData.objects.create(
            author=self.author,
            subject='Test',
            text='Text',
        )
        Message.objects.create(
            messagedata=messagedata,
            recipient=self.author,
            status=Message.STATUS_TRASHED,
            trashed_date=datetime.utcnow(),
        )

        expunge_private_messages()

        self.assertTrue(Message.objects.trashed().exists())
