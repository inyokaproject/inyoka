# -*- coding: utf-8 -*-
"""
    tests.apps.privmsg.test_models
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test privmsg models.

    :copyright: (c) 2011-2016 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime
from unittest import skip
from django.db.models import Q

from inyoka.privmsg.models import Message, MessageData
from inyoka.portal.user import User
from inyoka.utils.test import TestCase


@skip
class TestMessageQuerySet(TestCase):
    def setUp(self):
        self.author = User.objects.register_user('author', 'author', 'author', False)
        self.recipient = User.objects.register_user('recipient', 'recipient', 'recipient', False)
        self.subject = 'Testsubject'
        self.text = 'TestText'

    def test_messagequeryset_for_user(self):
        self.assertEqual(list(Message.objects.for_user(self.author)),
                         [])

    def test_messagequeryset_from_user(self):
        self.assertEqual(list(Message.objects.for_user(self.author)),
                         [])

    def test_messagequeryset_archived(self):
        self.assertEqual(list(Message.objects.for_user(self.author).archived()),
                         [])

    def test_messagequeryset_inboxed(self):
        self.assertEqual(list(Message.objects.for_user(self.author).inbox()),
                         [])

    def test_messagequeryset_sent(self):
        self.assertEqual(list(Message.objects.for_user(self.author).sent()),
                         [])

    def test_messagequeryset_trashed(self):
        self.assertEqual(list(Message.objects.for_user(self.author).trashed()),
                         [])

    def test_messagequeryset_deleted(self):
        self.assertEqual(list(Message.objects.for_user(self.author).deleted()),
                         [])

    def test_messagequeryset_read(self):
        self.assertEqual(list(Message.objects.for_user(self.author).read()),
                         [])

    def test_messagequeryset_unread(self):
        self.assertEqual(list(Message.objects.for_user(self.author).unread()),
                         [])

    def test_messagequeryset_to_expunge(self):
        self.assertEqual(list(Message.objects.for_user(self.author).to_expunge()),
                         [])


class TestMessageModel(TestCase):
    def setUp(self):
        self.author = User.objects.register_user('author', 'author', 'author', False)
        self.recipient = User.objects.register_user('recipient', 'recipient', 'recipient', False)
        self.subject = 'Testsubject'
        self.text = 'TestText'
        self.messagedata = MessageData.objects.create(author=self.author,
                                                 subject=self.subject,
                                                 text=self.text)
        self.messagedata.send(recipients=[self.recipient])
        self.message = Message.objects.for_user(self.recipient).first()
        self.sent_message = Message.objects.for_user(self.author).first()

    def test_message_get_absolute_url(self):
        self.assertEqual(self.sent_message.get_absolute_url(),
                         u'/messages/1/')
        self.assertEqual(self.message.get_absolute_url(),
                         u'/messages/2/')
        self.assertEqual(self.message.get_absolute_url('archive'),
                         u'/messages/2/archive/')
        self.assertEqual(self.message.get_absolute_url('delete'),
                         u'/messages/2/delete/')
        self.assertEqual(self.message.get_absolute_url('forward'),
                         u'/messages/2/forward/')
        self.assertEqual(self.message.get_absolute_url('restore'),
                         u'/messages/2/restore/')
        self.assertEqual(self.message.get_absolute_url('reply'),
                         u'/messages/2/reply/')
        self.assertEqual(self.message.get_absolute_url('trash'),
                         u'/messages/2/trash/')
        self.assertEqual(self.message.get_absolute_url('reply_to_all'),
                         u'/messages/2/reply/all/')
        self.assertEqual(self.sent_message.get_absolute_url('folder'),
                         u'/messages/sent/')
        self.assertEqual(self.message.get_absolute_url('folder'),
                         u'/messages/inbox/')

    def test_message_is_unread(self):
        self.assertFalse(self.sent_message.is_unread)
        self.assertTrue(self.message.is_unread)

    def test_message_is_own_message(self):
        self.assertTrue(self.sent_message.is_own_message)
        self.assertFalse(self.message.is_own_message)

    def test_message_author(self):
        self.assertEqual(self.message.author, self.author)
        self.assertEqual(self.sent_message.author, self.author)

    def test_message_recipients(self):
        self.assertListEqual(list(self.message.recipients), [self.recipient])

    def test_message_subject(self):
        self.assertEqual(self.message.subject, self.subject)

    def test_message_text(self):
        self.assertEqual(self.message.text, self.text)

    def test_message_text_rendered(self):
        self.assertEqual(self.message.text_rendered,
                         MessageData.get_text_rendered(self.text))

    def test_message_pub_date(self):
        # umm ... mock?
        # self.assertEqual(self.message.pub_date, datetime.utcnow())
        pass

    def test_message_mark_read(self):
        self.message.mark_read()
        self.assertFalse(self.message.is_unread)
        # mock datetime.utcnow() to make this work:
        # self.assertEqual(self.message.read_date, datetime.utcnow())

    def test_message_folder(self):
        self.assertEqual(self.message.folder, 'inbox')
        self.assertEqual(self.sent_message.folder, 'sent')

    def test_message_archive(self):
        self.message.archive()
        self.assertEqual(self.message.status, Message.MESSAGE_ARCHIVED)

    def test_message_trash(self):
        self.message.trash()
        self.assertEqual(self.message.status, Message.MESSAGE_TRASHED)
        # self.assertEqual(self.message.trashed_date, datetime.utcnow())

    def test_message_restore_sent_message(self):
        pass

    def test_message_restore_received_message(self):
        pass

@skip
class TestMessageData(TestCase):
    def setUp(self):
        pass

    def test_messagedata_send(self):
        # mock send_notification
        pass
