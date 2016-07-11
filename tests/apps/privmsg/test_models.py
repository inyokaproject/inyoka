# -*- coding: utf-8 -*-
"""
    tests.apps.privmsg.test_models
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test privmsg models.

    :copyright: (c) 2011-2016 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime, timedelta

from django.core.urlresolvers import reverse
from inyoka.portal.user import User
from inyoka.privmsg.models import Message, MessageData
from inyoka.utils.test import TestCase
# from unittest import skip
from mock import Mock, patch


class TestMessageQuerySet(TestCase):
    """Unit Tests for MessageQuerySet."""

    @classmethod
    def setUpClass(cls):
        yesterday = datetime.utcnow() - timedelta(days=1)
        cls.author = User.objects.register_user(
            username='author',
            email='author',
            password='',
            send_mail=True,
        )
        cls.recipient = User.objects.register_user(
            username='recipient',
            email='recipient',
            password='',
            send_mail=True,
        )
        cls.subject = u'Test'
        cls.text = u'Text'
        cls.messagedata = MessageData.objects.create(
            author=cls.author,
            subject=cls.subject,
            text=cls.text,
        )
        cls.sent_message = Message.objects.create(
            messagedata=cls.messagedata,
            recipient=cls.author,
            status=Message.STATUS_SENT,
        )
        cls.read_message = Message.objects.create(
            messagedata=cls.messagedata,
            recipient=cls.recipient,
            status=Message.STATUS_READ,
        )
        cls.unread_message = Message.objects.create(
            messagedata=cls.messagedata,
            recipient=cls.recipient,
            status=Message.STATUS_UNREAD,
        )
        cls.archived_message = Message.objects.create(
            messagedata=cls.messagedata,
            recipient=cls.recipient,
            status=Message.STATUS_ARCHIVED,
        )
        cls.trashed_message = Message.objects.create(
            messagedata=cls.messagedata,
            recipient=cls.recipient,
            status=Message.STATUS_TRASHED,
            trashed_date=yesterday,
        )

    @classmethod
    def tearDownClass(cls):
        Message.objects.all().delete()
        MessageData.objects.all().delete()
        cls.author.delete()
        cls.recipient.delete()

    def test_messagequeryset_for_user(self):
        """Test `for_user()` should return all messages received by the given user."""
        expected_values = [self.sent_message]
        actual_values = Message.objects.for_user(self.author)
        self.assertItemsEqual(actual_values, expected_values)

    def test_messagequeryset_from_user(self):
        """Test `from_user()` should return all messages sent by the given user."""
        expected_values = [
            self.sent_message,
            self.read_message,
            self.unread_message,
            self.archived_message,
            self.trashed_message,
        ]
        actual_values = Message.objects.from_user(self.author)
        self.assertItemsEqual(actual_values, expected_values)

    def test_messagequeryset_inboxed(self):
        """Test `inboxed()` should return all messages in the inbox (read or unread)"""
        expected_values = [self.read_message, self.unread_message]
        actual_values = Message.objects.inboxed()
        self.assertItemsEqual(actual_values, expected_values)

    def test_messagequeryset_read(self):
        """Test `read()` should return all read messages."""
        expected_values = [self.read_message]
        actual_values = Message.objects.read()
        self.assertItemsEqual(actual_values, expected_values)

    def test_messagequeryset_unread(self):
        """Test `unread()` should return all unread messages."""
        expected_values = [self.unread_message]
        actual_values = Message.objects.unread()
        self.assertItemsEqual(actual_values, expected_values)

    def test_messagequeryset_sent(self):
        """Test `sent()` should return the list of all sent messages."""
        expected_values = [self.sent_message]
        actual_values = Message.objects.sent()
        self.assertItemsEqual(actual_values, expected_values)

    def test_messagequeryset_archived(self):
        """Test `archived()` should return all archived messages."""
        expected_values = [self.archived_message]
        actual_values = Message.objects.archived()
        self.assertItemsEqual(actual_values, expected_values)

    def test_messagequeryset_trashed(self):
        """Test `trashed()` should return all trashed messages."""
        expected_values = [self.trashed_message]
        actual_values = Message.objects.trashed()
        self.assertItemsEqual(actual_values, expected_values)

    def test_messagequeryset_to_expunge(self):
        """Test `to_expunge()` should return trashed messages older than the grace period."""
        expected_values = [self.trashed_message]
        actual_values = Message.objects.to_expunge()
        self.assertItemsEqual(actual_values, expected_values)

    def test_messagequeryset_to_expunge_with_younger_message(self):
        """Test `to_expunge()` should ignore trashed messages younger than the grace period."""
        self.trashed_message.trashed_date = datetime.utcnow()
        self.trashed_message.save()
        expected_values = []

        actual_values = Message.objects.to_expunge()

        self.assertItemsEqual(actual_values, expected_values)

    def test_messagequeryset_bulk_archive(self):
        """Test `bulk_archive()` should give all messages in the queryset the "archived" status."""
        Message.objects.filter(pk=self.sent_message.id).bulk_archive()

        self.sent_message = Message.objects.get(pk=self.sent_message.id)
        self.assertEqual(self.sent_message.status, Message.STATUS_ARCHIVED)

    @patch('inyoka.privmsg.models.datetime')
    def test_messagequeryset_bulk_trash(self, mock_datetime):
        """Test `bulk_trash()` should mark all messages as "trashed" and set their trashed_date."""
        expected_datetime = datetime.utcnow()
        mock_datetime.utcnow.return_value = expected_datetime
        queryset = Message.objects.filter(pk=self.sent_message.id)

        queryset.bulk_trash()

        self.sent_message = Message.objects.get(pk=self.sent_message.id)
        self.assertEqual(self.sent_message.status, Message.STATUS_TRASHED)
        self.assertEqual(self.sent_message.trashed_date, expected_datetime)

    def test_messagequeryset_bulk_restore_with_sent_message(self):
        """Test `bulk_restore` should remove trashed_date and reset sent messages to status: sent."""
        self.sent_message.trash()

        Message.objects.filter(pk=self.sent_message.id).bulk_restore()

        self.sent_message = Message.objects.get(pk=self.sent_message.id)
        self.assertEqual(self.sent_message.status, Message.STATUS_SENT)
        self.assertIsNone(self.sent_message.trashed_date)

    def test_messagequeryset_bulk_restore_with_received_message(self):
        """Test `bulk_restore` should remove trashed_date and reset received messages to status: read."""
        self.read_message.trash()

        Message.objects.filter(pk=self.read_message.id).bulk_restore()

        self.read_message = Message.objects.get(pk=self.read_message.id)
        self.assertEqual(self.read_message.status, Message.STATUS_READ)
        self.assertIsNone(self.read_message.trashed_date)


class TestMessageModel(TestCase):
    """Unit Tests for the Message model"""

    # Running just the tests for privmsg without this line: works
    # Running the full test suite without this line: fails
    urls = 'inyoka.portal.urls'

    def setUp(self):
        self.author = User(username='author')
        self.recipient = User(username='recipient')
        self.subject = 'TestSubject'
        self.text = 'TestText'
        self.text_rendered = MessageData.get_text_rendered(self.text)
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

    def test_messagemodel_is_unread_with_unread_message(self):
        """Test `is_unread` returns True when message is unread."""
        self.assertTrue(self.unread_message.is_unread)

    def test_messagemodel_is_unread_with_read_message(self):
        """Test `is_unread` returns False when message was read."""
        self.assertFalse(self.read_message.is_unread)

    def test_messagemodel_is_own_message_with_sent_message(self):
        """Test `is_own_message` returns True when message was sent (author==recipient)."""
        self.assertTrue(self.sent_message.is_own_message)

    def test_messagemodel_is_own_message_with_received_message(self):
        """Test `is_own_message` returns False when message was received."""
        self.assertFalse(self.read_message.is_own_message)

    def test_messagemodel_author(self):
        """Test `author` correctly relays date from messagedata."""
        self.assertEqual(self.sent_message.author, self.author)

    def test_messagemodel_recipients(self):
        """Test `recipients` correctly relays original_recipients from the messagedata."""
        # this needs to somehow mock the m2m relation

    def test_messagemodel_subject(self):
        """Test `subject` correctly relays date from messagedata."""
        self.assertEqual(self.sent_message.subject, self.subject)

    def test_messagemodel_text(self):
        """Test `text` correctly relays date from messagedata."""
        self.assertEqual(self.sent_message.text, self.text)

    def test_messagemodel_text_rendered(self):
        """Test `text_rendered` returns the rendered text."""
        self.assertEqual(self.sent_message.text_rendered, self.text_rendered)

    def test_messagemodel_pub_date(self):
        """Test `pub_date` correctly relays date from messagedata."""
        self.assertEqual(self.sent_message.pub_date, self.pub_date)

    def test_messagemodel_folder_with_read_message(self):
        """Test `get_absolute_url()` returns correct url when action='folder' on a read message."""
        self.assertEqual(self.read_message.folder, 'inbox')

    def test_messagemodel_folder_with_unread_message(self):
        """Test `get_absolute_url()` returns correct url when action='folder' on an unread message."""
        self.assertEqual(self.unread_message.folder, 'inbox')

    def test_messagemodel_folder_with_sent_message(self):
        """Test `get_absolute_url()` returns correct url when action='folder' on a sent message."""
        self.assertEqual(self.sent_message.folder, 'sent')

    def test_messagemodel_folder_with_archived_message(self):
        """Test `get_absolute_url()` returns correct url when action='folder' on an archived message."""
        self.assertEqual(self.archived_message.folder, 'archive')

    def test_messagemodel_folder_with_trashed_message(self):
        self.assertEqual(self.trashed_message.folder, 'trash')

    def test_messagemodel_get_absolute_url_with_action_archive(self):
        """Test `get_absolute_url()` returns correct url when action='archive'."""
        expected_value = reverse('privmsg-message-archive', args=[self.read_message.pk])
        actual_value = self.read_message.get_absolute_url('archive')
        self.assertEqual(actual_value, expected_value)

    def test_messagemodel_get_absolute_url_with_action_delete(self):
        """Test `get_absolute_url()` returns correct url when action='delete'."""
        expected_value = reverse('privmsg-message-delete', args=[self.read_message.pk])
        actual_value = self.read_message.get_absolute_url('delete')
        self.assertEqual(actual_value, expected_value)

    def test_messagemodel_get_absolute_url_with_action_forward(self):
        """Test `get_absolute_url()` returns correct url when action='forward'."""
        expected_value = reverse('privmsg-message-forward', args=[self.read_message.pk])
        actual_value = self.read_message.get_absolute_url('forward')
        self.assertEqual(actual_value, expected_value)

    def test_messagemodel_get_absolute_url_with_action_restore(self):
        """Test `get_absolute_url()` returns correct url when action='restore'."""
        expected_value = reverse('privmsg-message-restore', args=[self.read_message.pk])
        actual_value = self.read_message.get_absolute_url('restore')
        self.assertEqual(actual_value, expected_value)

    def test_messagemodel_get_absolute_url_with_action_reply(self):
        """Test `get_absolute_url()` returns correct url when action='reply'."""
        expected_value = reverse('privmsg-message-reply', args=[self.read_message.pk])
        actual_value = self.read_message.get_absolute_url('reply')
        self.assertEqual(actual_value, expected_value)

    def test_messagemodel_get_absolute_url_with_action_reply_to_all(self):
        """Test `get_absolute_url()` returns correct url when action='reply_to_all'."""
        expected_value = reverse('privmsg-message-reply-all', args=[self.read_message.pk])
        actual_value = self.read_message.get_absolute_url('reply_to_all')
        self.assertEqual(actual_value, expected_value)

    def test_messagemodel_get_absolute_url_with_action_trash(self):
        """Test `get_absolute_url()` returns correct url when action='trash'."""
        expected_value = reverse('privmsg-message-trash', args=[self.read_message.pk])
        actual_value = self.read_message.get_absolute_url('trash')
        self.assertEqual(actual_value, expected_value)

    def test_messagemodel_get_absolute_url_with_action_folder(self):
        """Test `get_absolute_url()` returns correct url when action='folder' on a read message."""
        expected_value = reverse('privmsg-inbox')
        actual_value = self.read_message.get_absolute_url('folder')
        self.assertEqual(actual_value, expected_value)

    def test_messagemodel_get_absolute_url_with_action_folder_on_sent_message(self):
        """Test `get_absolute_url()` returns correct url when action='folder' on a sent message."""
        expected_value = reverse('privmsg-sent')
        actual_value = self.sent_message.get_absolute_url('folder')
        self.assertEqual(actual_value, expected_value)

    def test_messagemodel_get_absolute_url_with_action_show(self):
        """Test `get_absolute_url()` returns correct url when action='show'"""
        expected_value = reverse('privmsg-message', args=[self.read_message.pk])
        actual_value = self.read_message.get_absolute_url('show')
        self.assertEqual(actual_value, expected_value)

    @patch('inyoka.privmsg.models.Message.save')
    @patch('inyoka.privmsg.models.datetime')
    def test_messagemodel_mark_read(self, mock_datetime, mock_save):
        """Test `mark_read()` correctly sets read_date and status to read."""
        expected_time = datetime.utcnow()
        mock_datetime.utcnow.return_value = expected_time
        self.unread_message.mark_read()

        self.assertFalse(self.unread_message.is_unread)
        self.assertEqual(self.unread_message.read_date, expected_time)
        self.assertTrue(mock_save.called)

    @patch('inyoka.privmsg.models.Message.save')
    def test_messagemodel_mark_read_on_read_message(self, mock_save):
        """Test `mark_read()` does nothing on messages that are already marked as read."""
        self.read_message.mark_read()
        self.assertFalse(mock_save.called)

    @patch('inyoka.privmsg.models.Message.save')
    def test_messagemodel_archive(self, mock_save):
        """Test `archive()` correctly sets status to archived."""
        self.read_message.archive()
        self.assertEqual(self.read_message.status, Message.STATUS_ARCHIVED)
        self.assertTrue(mock_save.called)

    @patch('inyoka.privmsg.models.Message.save')
    @patch('inyoka.privmsg.models.User.privmsg_count')
    def test_messagemodel_archive_on_unread_message(self, mock_save, mock_privmsg_count):
        """Test `archive()` correctly decrements unread privmsg-count when called on unread messages."""
        self.unread_message.archive()
        self.assertTrue(mock_privmsg_count.called)

    @patch('inyoka.privmsg.models.Message.save')
    @patch('inyoka.privmsg.models.datetime')
    def test_messagemodel_trash(self, mock_datetime, mock_save):
        """Test `trash()` method correctly sets trashed status and trashed_date."""
        expected_time = datetime.utcnow()
        mock_datetime.utcnow.return_value = expected_time

        self.unread_message.trash()

        self.assertEqual(self.unread_message.status, Message.STATUS_TRASHED)
        self.assertEqual(self.unread_message.trashed_date, expected_time)
        self.assertTrue(mock_save.called)

    @patch('inyoka.privmsg.models.Message.save')
    def test_messagemodel_restore_with_received_message(self, mock_save):
        """Test `restore()` returns sent message to read status."""
        message = Message(
            messagedata=self.messagedata,
            recipient=self.recipient,
            status=Message.STATUS_ARCHIVED,
        )

        message.restore()

        self.assertEqual(message.status, Message.STATUS_READ)
        self.assertTrue(mock_save.called)

    @patch('inyoka.privmsg.models.Message.save')
    def test_messagemodel_restore_with_sent_message(self, mock_save):
        """Test `restore()` returns sent message to sent status."""
        message = Message(
            messagedata=self.messagedata,
            recipient=self.author,
            status=Message.STATUS_ARCHIVED,
        )

        message.restore()

        self.assertEqual(message.status, Message.STATUS_SENT)
        self.assertTrue(mock_save.called)

    @patch('inyoka.privmsg.models.Message.save')
    def test_messagemodel_restore_from_trash_with_received_message(self, mock_save):
        """Test `restore()` returns received message to unread status and unsets trashed_date."""
        self.trashed_message.restore()

        self.assertEqual(self.trashed_message.status, Message.STATUS_READ)
        self.assertIsNone(self.trashed_message.trashed_date)
        self.assertTrue(mock_save.called)

    @patch('inyoka.privmsg.models.Message.save')
    def test_messagemodel_restore_from_trash_with_sent_message(self, mock_save):
        """Test `restore()` returns sent message to sent status and unsets trashed_date."""
        self.sent_message.status = Message.STATUS_TRASHED

        self.sent_message.restore()

        self.assertEqual(self.sent_message.status, Message.STATUS_SENT)
        self.assertIsNone(self.sent_message.trashed_date)
        self.assertTrue(mock_save.called)


class TestMessageDataManager(TestCase):
    """Test MessageDataManager"""

    def setUp(self):
        self.author = User.objects.register_user(
            username='author',
            email='author',
            password='',
            send_mail=True,
        )
        self.messagedata = MessageData.objects.create(
            author=self.author,
            subject='Test',
            text='Text',
        )

    def test_messagedatamanager_abandoned(self):
        """Test `abandoned()` returns list of messagedata objects that have no associated messages."""
        expected_values = [self.messagedata]

        actual_values = MessageData.objects.abandoned()

        self.assertItemsEqual(actual_values, expected_values)


class TestMessageData(TestCase):
    """Test MessageData"""

    # This is complicated to mock :( Might just write it as implementation test.
    # @patch('inyoka.privmsg.models.Message.objects.create')
    # @patch('inyoka.privmsg.models.MessageData.objects.create')
    # def test_messagedata_send(self, mock_messagedata, mock_message):
    #     author = User(username='author')
    #     recipient = User(username='recipient')
    #     mock_message.return_value = Message()
    #     mock_messagedata.return_value = MessageData()
    #     pass
