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
    """
    Tests for privmsg tasks.
    """
    def test_clean_abandoned_messages(self):
        """
        clean_abandoned_messages() should delete messages that are no longer referenced by any users.
        """
        author = User.objects.register_user(
            username='author',
            email='author',
            password='',
            send_mail=False,
        )
        MessageData.objects.create(author=author, subject='Test', text='Text')

        clean_abandoned_messages()

        self.assertFalse(MessageData.objects.abandoned().exists())

    def test_expunge_private_messages(self):
        """
        expunde_private_messages() should delete trashed messages after a grace period (defined in settings).
        """
        yesterday = datetime.utcnow() - timedelta(days=1)
        author = User.objects.register_user(
            username='author',
            email='author',
            password='',
            send_mail=False,
        )
        messagedata = MessageData.objects.create(
            author=author,
            subject='Test',
            text='Text',
        )
        Message.objects.create(
            messagedata=messagedata,
            recipient=author,
            status=Message.STATUS_TRASHED,
            trashed_date=yesterday,
        )

        expunge_private_messages()

        self.assertFalse(Message.objects.trashed().exists())

    def test_expunge_private_messages_with_newer(self):
        """
        expunde_private_messages() should not delete trashed messages before the grace period is over.
        """
        author = User.objects.register_user(
            username='author',
            email='author',
            password='',
            send_mail=False,
        )
        messagedata = MessageData.objects.create(
            author=author,
            subject='Test',
            text='Text',
        )
        Message.objects.create(
            messagedata=messagedata,
            recipient=author,
            status=Message.STATUS_TRASHED,
            trashed_date=datetime.utcnow(),
        )

        expunge_private_messages()

        self.assertTrue(Message.objects.trashed().exists())
