# -*- coding: utf-8 -*-
"""
    tests.apps.privmsg.test_models
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test privmsg models.

    :copyright: (c) 2011-2016 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime, timedelta
# from unittest import skip
from mock import patch

from django.core.urlresolvers import reverse

from inyoka.privmsg.models import Message, MessageData
from inyoka.portal.user import User
from inyoka.utils.test import TestCase


class TestMessageQuerySet(TestCase):
    """
    Unit Tests for MessageQuerySet.
    """

    @classmethod
    def setUpClass(self):
        yesterday = datetime.utcnow() - timedelta(days=1)
        self.author = User.objects.register_user(
            username='author',
            email='author',
            password='',
            send_mail=True,
        )
        self.recipient = User.objects.register_user(
            username='recipient',
            email='recipient',
            password='',
            send_mail=True,
        )
        self.subject = u'Test'
        self.text = u'Text'
        self.messagedata = MessageData.objects.create(
            author=self.author,
            subject=self.subject,
            text=self.text,
        )
        self.sent_message = Message.objects.create(
            messagedata=self.messagedata,
            recipient=self.author,
            status=Message.STATUS_SENT,
        )
        self.read_message = Message.objects.create(
            messagedata=self.messagedata,
            recipient=self.recipient,
            status=Message.STATUS_READ,
        )
        self.unread_message = Message.objects.create(
            messagedata=self.messagedata,
            recipient=self.recipient,
            status=Message.STATUS_UNREAD,
        )
        self.archived_message = Message.objects.create(
            messagedata=self.messagedata,
            recipient=self.recipient,
            status=Message.STATUS_ARCHIVED,
        )
        self.trashed_message = Message.objects.create(
            messagedata=self.messagedata,
            recipient=self.recipient,
            status=Message.STATUS_TRASHED,
            trashed_date=yesterday,
        )
        self.deleted_message = Message.objects.create(
            messagedata=self.messagedata,
            recipient=self.recipient,
            status=Message.STATUS_DELETED,
        )

    @classmethod
    def tearDownClass(self):
        pass

    def test_messagequeryset_for_user(self):
        """
        Test
        """
        expected_values = [self.sent_message]
        actual_values = Message.objects.for_user(self.author)
        self.assertItemsEqual(actual_values, expected_values)

    def test_messagequeryset_from_user(self):
        """
        Test
        """
        expected_values = [
            self.sent_message,
            self.read_message,
            self.unread_message,
            self.archived_message,
            self.trashed_message,
            self.deleted_message,
        ]
        actual_values = Message.objects.from_user(self.author)
        self.assertItemsEqual(actual_values, expected_values)

    def test_messagequeryset_inboxed(self):
        """
        Test
        """
        expected_values = [self.read_message, self.unread_message]
        actual_values = Message.objects.inboxed()
        self.assertItemsEqual(actual_values, expected_values)

    def test_messagequeryset_read(self):
        """
        Test
        """
        expected_values = [self.read_message]
        actual_values = Message.objects.read()
        self.assertItemsEqual(actual_values, expected_values)

    def test_messagequeryset_unread(self):
        """
        Test
        """
        expected_values = [self.unread_message]
        actual_values = Message.objects.unread()
        self.assertItemsEqual(actual_values, expected_values)

    def test_messagequeryset_sent(self):
        """
        Test
        """
        expected_values = [self.sent_message]
        actual_values = Message.objects.sent()
        self.assertItemsEqual(actual_values, expected_values)

    def test_messagequeryset_archived(self):
        """
        Test
        """
        expected_values = [self.archived_message]
        actual_values = Message.objects.archived()
        self.assertItemsEqual(actual_values, expected_values)

    def test_messagequeryset_trashed(self):
        """
        Test
        """
        expected_values = [self.trashed_message]
        actual_values = Message.objects.trashed()
        self.assertItemsEqual(actual_values, expected_values)

    def test_messagequeryset_deleted(self):
        """
        Test
        """
        expected_values = [self.deleted_message]
        actual_values = Message.objects.deleted()
        self.assertItemsEqual(actual_values, expected_values)

    def test_messagequeryset_to_expunge(self):
        """
        Test
        """
        expected_values = [self.trashed_message]
        actual_values = Message.objects.to_expunge()
        self.assertItemsEqual(actual_values, expected_values)


class TestMessageModel(TestCase):
    """
    Unit Tests for the Message model
    """

    def setUp(self):
        self.author = User(username='author')
        self.recipient = User(username='recipient')
        self.subject = 'TestSubject'
        self.text = 'TestText'
        self.pub_date = datetime.utcnow()
        self.messagedata = MessageData(
            pk=1,
            author=self.author,
            subject=self.subject,
            text=self.text,
            pub_date=self.pub_date,
        )
        self.sent_message = Message(
            pk=1,
            messagedata=self.messagedata,
            recipient=self.author,
            status=Message.STATUS_SENT,
        )
        self.read_message = Message(
            pk=2,
            messagedata=self.messagedata,
            recipient=self.recipient,
            status=Message.STATUS_READ,
        )
        self.unread_message = Message(
            pk=3,
            messagedata=self.messagedata,
            recipient=self.recipient,
            status=Message.STATUS_UNREAD,
        )
        self.archived_message = Message(
            pk=4,
            messagedata=self.messagedata,
            recipient=self.recipient,
            status=Message.STATUS_ARCHIVED,
        )
        self.trashed_message = Message(
            pk=5,
            messagedata=self.messagedata,
            recipient=self.recipient,
            status=Message.STATUS_TRASHED,
        )

    @classmethod
    def tearDownClass(self):
        pass

    def test_messagemodel_is_unread_with_unread_message(self):
        self.assertTrue(self.unread_message.is_unread)

    def test_messagemodel_is_unread_with_read_message(self):
        self.assertFalse(self.read_message.is_unread)

    def test_messagemodel_is_own_message_with_sent_message(self):
        self.assertTrue(self.sent_message.is_own_message)

    def test_messagemodel_is_own_message_with_received_message(self):
        self.assertFalse(self.read_message.is_own_message)

    def test_messagemodel_author(self):
        self.assertEqual(self.sent_message.author, self.author)

    # def test_messagemodel_recipients(self):
    #     # this needs to somehow mock the m2m relation

    def test_messagemodel_subject(self):
        self.assertEqual(self.sent_message.subject, self.subject)

    def test_messagemodel_text(self):
        self.assertEqual(self.sent_message.text, self.text)

    # def test_messagemodel_text_rendered(self):
    #     # shouldn't be a problem, but I need the rendered text

    def test_messagemodel_pub_date(self):
        self.assertEqual(self.sent_message.pub_date, self.pub_date)

    def test_messagemodel_folder_with_read_message(self):
        self.assertEqual(self.read_message.folder, 'inbox')

    def test_messagemodel_folder_with_unread_message(self):
        self.assertEqual(self.unread_message.folder, 'inbox')

    def test_messagemodel_folder_with_sent_message(self):
        self.assertEqual(self.sent_message.folder, 'sent')

    def test_messagemodel_folder_with_archived_message(self):
        self.assertEqual(self.archived_message.folder, 'archive')

    def test_messagemodel_folder_with_trashed_message(self):
        self.assertEqual(self.trashed_message.folder, 'trash')

    def test_messagemodel_get_absolute_url_with_action_archive(self):
        expected_value = reverse('privmsg-message-archive', args=[self.read_message.id])
        actual_value = self.read_message.get_absolute_url('archive')
        self.assertEqual(actual_value, expected_value)

    def test_messagemodel_get_absolute_url_with_action_delete(self):
        expected_value = reverse('privmsg-message-delete', args=[self.read_message.id])
        actual_value = self.read_message.get_absolute_url('delete')
        self.assertEqual(actual_value, expected_value)

    def test_messagemodel_get_absolute_url_with_action_forward(self):
        expected_value = reverse('privmsg-message-forward', args=[self.read_message.id])
        actual_value = self.read_message.get_absolute_url('forward')
        self.assertEqual(actual_value, expected_value)

    def test_messagemodel_get_absolute_url_with_action_restore(self):
        expected_value = reverse('privmsg-message-restore', args=[self.read_message.id])
        actual_value = self.read_message.get_absolute_url('restore')
        self.assertEqual(actual_value, expected_value)

    def test_messagemodel_get_absolute_url_with_action_reply(self):
        expected_value = reverse('privmsg-message-reply', args=[self.read_message.id])
        actual_value = self.read_message.get_absolute_url('reply')
        self.assertEqual(actual_value, expected_value)

    def test_messagemodel_get_absolute_url_with_action_reply_to_all(self):
        expected_value = reverse('privmsg-message-reply-all', args=[self.read_message.id])
        actual_value = self.read_message.get_absolute_url('reply_to_all')
        self.assertEqual(actual_value, expected_value)

    def test_messagemodel_get_absolute_url_with_action_trash(self):
        expected_value = reverse('privmsg-message-trash', args=[self.read_message.id])
        actual_value = self.read_message.get_absolute_url('trash')
        self.assertEqual(actual_value, expected_value)

    def test_messagemodel_get_absolute_url_with_action_folder(self):
        expected_value = reverse('privmsg-inbox')
        actual_value = self.read_message.get_absolute_url('folder')
        self.assertEqual(actual_value, expected_value)

    def test_messagemodel_get_absolute_url_with_action_show(self):
        expected_value = reverse('privmsg-message', args=[self.read_message.id])
        actual_value = self.read_message.get_absolute_url('show')
        self.assertEqual(actual_value, expected_value)

    @patch('inyoka.privmsg.models.Message.save')
    @patch('inyoka.privmsg.models.datetime')
    def test_messagemodel_mark_read(self, mock_datetime, mock_save):
        expected_time = datetime.utcnow()
        mock_datetime.utcnow.return_value = expected_time
        self.unread_message.mark_read()

        self.assertFalse(self.unread_message.is_unread)
        self.assertEqual(self.unread_message.read_date, expected_time)

    @patch('inyoka.privmsg.models.Message.save')
    def test_messagemodel_archive(self, mock_save):
        self.unread_message.archive()
        self.assertEqual(self.unread_message.status, Message.STATUS_ARCHIVED)

    @patch('inyoka.privmsg.models.Message.save')
    @patch('inyoka.privmsg.models.datetime')
    def test_messagemodel_trash(self, mock_datetime, mock_save):
        expected_time = datetime.utcnow()
        mock_datetime.utcnow.return_value = expected_time
        self.unread_message.trash()

        self.assertEqual(self.unread_message.status, Message.STATUS_TRASHED)
        self.assertEqual(self.unread_message.trashed_date, expected_time)

    @patch('inyoka.privmsg.models.Message.save')
    def test_messagemodel_restore_with_received_message(self, mock_save):
        message = Message(messagedata=self.messagedata, recipient=self.recipient, status=Message.STATUS_ARCHIVED)
        message.restore()
        self.assertEqual(message.status, Message.STATUS_READ)

    @patch('inyoka.privmsg.models.Message.save')
    def test_messagemodel_restore_with_sent_message(self, mock_save):
        message = Message(messagedata=self.messagedata, recipient=self.author, status=Message.STATUS_ARCHIVED)
        message.restore()
        self.assertEqual(message.status, Message.STATUS_SENT)

    @patch('inyoka.privmsg.models.Message.save')
    def test_messagemodel_restore_from_trash_with_received_message(self, mock_save):
        self.trashed_message.restore()
        self.assertEqual(self.trashed_message.status, Message.STATUS_READ)
        self.assertIsNone(self.trashed_message.trashed_date)

    @patch('inyoka.privmsg.models.Message.save')
    def test_messagemodel_restore_from_trash_with_received_message(self, mock_save):
        self.sent_message.status = Message.STATUS_TRASHED
        self.sent_message.restore()
        self.assertEqual(self.sent_message.status, Message.STATUS_SENT)
        self.assertIsNone(self.sent_message.trashed_date)


class TestMessageDataManager(TestCase):
    """
    Test MessageDataManager
    """

    def test_messagedatamanager_abandoned(self):
        """
        Test that abandoned() method returns list of messagedata objects that have no messages assigned to them.
        """
        author = User.objects.register_user(
            username='author',
            email='author',
            password='',
            send_mail=True,
        )
        messagedata = MessageData.objects.create(
            author=author,
            subject='Test',
            text='Text',
        )
        expected_values = [messagedata]

        actual_values = MessageData.objects.abandoned()

        self.assertItemsEqual(actual_values, expected_values)


class TestMessageData(TestCase):
    """
    Test MessageData
    """

    # This is complicated to mock :( Might just write it as implementation test.
    # @patch('inyoka.privmsg.models.Message.objects.create')
    # @patch('inyoka.privmsg.models.MessageData.objects.create')
    # def test_messagedata_send(self, mock_messagedata, mock_message):
    #     author = User(username='author')
    #     recipient = User(username='recipient')
    #     mock_message.return_value = Message()
    #     mock_messagedata.return_value = MessageData()
    #     pass
