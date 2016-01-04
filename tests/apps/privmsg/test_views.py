# -*- coding: utf-8 -*-
"""
    tests.apps.privmsg.test_views
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test privmsg views.

    :copyright: (c) 2011-2016 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from unittest import skip

from inyoka.privmsg.views import (
    InboxedMessagesView,
    SentMessagesView,
    ArchivedMessagesView,
    TrashedMessagesView,
    ReadMessagesView,
    UnreadMessagesView,
    MessageToArchiveView,
    MessageToTrashView,
    MessageRestoreView,
    MessageDeleteView,
    MessageComposeView,
    MessageReplyView,
    MessageForwardView,
    MessageReplyReportedTopicView,
    MessageReplySuggestedArticleView,
)
from inyoka.utils.test import TestCase


@skip
class TestInboxedMessagesView(TestCase):
    def test_inboxedmessagesview_folder_in_context(self):
        context = InboxedMessagesView.get_context_data()
        self.assertIn('folder', context.keys())
        self.assertIn('folder_name', context.keys())
        self.assertEqual('inbox', context['folder'])
        self.assertEqual(u'Inbox', context['folder_name'])

    @skip
    def test_inboxedmessagesview_messages_in_context(self):
        pass


@skip
class TestSentMessagesView(TestCase):
    def test_sentmessagesview_folder_in_context(self):
        context = SentMessagesView.get_context_data()
        self.assertIn('folder', context.keys())
        self.assertIn('folder_name', context.keys())
        self.assertEqual('sent', context['folder'])
        self.assertEqual(u'Sent', context['folder_name'])

    @skip
    def test_sentmessagesview_messages_in_context(self):
        pass


@skip
class TestArchivedMessagesView(TestCase):
    def test_archivedmessagesview_folder_in_context(self):
        context = ArchivedMessagesView.get_context_data()
        self.assertIn('folder', context.keys())
        self.assertIn('folder_name', context.keys())
        self.assertEqual('archive', context['folder'])
        self.assertEqual(u'Archive', context['folder_name'])

    @skip
    def test_archivedmessagesview_messages_in_context(self):
        pass


@skip
class TestTrashedMessagesView(TestCase):
    def test_trashedmessagesview_folder_in_context(self):
        context = TrashedMessagesView.get_context_data()
        self.assertIn('folder', context.keys())
        self.assertIn('folder_name', context.keys())
        self.assertEqual('trash', context['folder'])
        self.assertEqual(u'Trash', context['folder_name'])

    @skip
    def test_trashedmessagesview_messages_in_context(self):
        pass


@skip
class TestReadMessagesView(TestCase):
    def test_readmessagesview_folder_in_context(self):
        context = ReadMessagesView.get_context_data()
        self.assertIn('folder', context.keys())
        self.assertIn('folder_name', context.keys())
        self.assertEqual('read', context['folder'])
        self.assertEqual(u'Read', context['folder_name'])

    @skip
    def test_readmessagesview_messages_in_context(self):
        pass


@skip
class TestUnreadMessagesView(TestCase):
    def test_unreadmessagesview_folder_in_context(self):
        context = UnreadMessagesView.get_context_data()
        self.assertIn('folder', context.keys())
        self.assertIn('folder_name', context.keys())
        self.assertEqual('unread', context['folder'])
        self.assertEqual(u'Unread', context['folder_name'])

    @skip
    def test_unreadmessagesview_messages_in_context(self):
        pass


@skip
class TestMessageView(TestCase):
    def test_messageview_get_object(self):
        pass


@skip
class TestMessageToArchiveView(TestCase):
    def test_messagetoarchiveview_confirm_action(self):
        pass


@skip
class TestMessageToTrashView(TestCase):
    pass


@skip
class TestMessageRestoreView(TestCase):
    pass


@skip
class TestMessageDeleteView(TestCase):
    pass


@skip
class TestMessageComposeView(TestCase):
    def test_messagecomposeview_get_form_kwargs(self):
        pass

    def test_messagecomposeview_form_valid(self):
        pass

    def test_messagecomposeview_get_initial(self):
        pass


@skip
class TestMessageReplyView(TestCase):
    def test_messagereplyview_get_initial(self):
        pass


@skip
class TestMessageForwardView(TestCase):
    def test_messageforwardview_get_initial(self):
        pass


@skip
class TestMessageReplyReportedTopicView(TestCase):
    def test_messagereplyreportedtopicview_get_initial(self):
        pass


@skip
class TestMessageReplySuggestedArticleView(TestCase):
    def test_messagereplysuggestedarticleview_get_initial(self):
        pass
