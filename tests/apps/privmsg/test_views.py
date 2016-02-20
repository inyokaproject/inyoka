# -*- coding: utf-8 -*-
"""
    tests.apps.privmsg.test_views
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test privmsg views.

    :copyright: (c) 2011-2016 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse_lazy
from django.http import Http404
from django.test import RequestFactory
from django.utils.translation import ugettext as _
from inyoka.portal.user import User
from inyoka.privmsg.forms import (
    MessageComposeForm,
    MultiMessageSelectForm,
    PrivilegedMessageComposeForm,
)
from inyoka.privmsg.views import (
    ArchivedMessagesView,
    BaseMessageComposeView,
    InboxedMessagesView,
    MessageComposeView,
    MessageDeleteView,
    MessageForwardView,
    MessageReplyReportedTopicView,
    MessageReplySuggestedArticleView,
    MessageReplyView,
    MessageRestoreView,
    MessagesFolderView,
    MessageToArchiveView,
    MessageToTrashView,
    MessageView,
    MultiMessageProcessView,
    ReadMessagesView,
    SentMessagesView,
    TrashedMessagesView,
    UnreadMessagesView,
)
from inyoka.utils.test import TestCase
from mock import Mock, call, patch


def setup_view(view, request, *args, **kwargs):
    """
    Mimic as_view() but returns a view instance.
    """
    view.request = request
    view.args = args
    view.kwargs = kwargs
    return view


class TestMessagesFolderView(TestCase):
    """
    Unit Tests for the MessagesFolderView base class.
    """

    def test_messagesfolderview_get_queryset_builds_correct_queryset(self):
        """
        Test that get_queryset() builds the correct queryset.
        """
        request = RequestFactory().get('/')
        request.user = Mock()
        view = MessagesFolderView(queryset_name='fake')
        view = setup_view(view, request)
        expected_calls = [call.message_set.fake(), call.message_set.fake().optimized()]

        view.get_queryset()

        request.user.assert_has_calls(expected_calls)

    def test_messagesfolderview_get_queryset_without_queryset_name(self):
        """
        Test that get_queryset() raises `ImproperlyConfigured` when `queryset_name` is not set.
        """
        request = RequestFactory().get('/')
        request.user = Mock()
        view = MessagesFolderView()
        view = setup_view(view, request)

        with self.assertRaises(ImproperlyConfigured):
            view.get_queryset()


class TestFolderMessagesViewIntegration(TestCase):
    """
    Integration Test for subclasses of MessagesFolderView.
    """
    urls = 'inyoka.portal.urls'

    def setUp(self):
        """
        Set up a user to test with.
        """
        self.user = User.objects.register_user(
            username='testuser',
            email='testuser',
            password='testuser',
            send_mail=False,
        )

    def test_inboxedmessagesview_as_user(self):
        """
        When called by a user, InboxedMessagesView should load and context_data be present.
        """
        request = RequestFactory().get('/messages/inbox/')
        request.user = self.user
        view = InboxedMessagesView.as_view()

        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['view'].folder, 'inbox')
        self.assertItemsEqual(response.context_data['messages'], [])
        self.assertFalse(response.context_data['is_paginated'])

    def test_inboxedmessagesview_as_anonymous(self):
        """
        When called by anonymous, InboxedMessagesView should redirect to login.
        """
        request = RequestFactory().get('/messages/inbox/')
        request.user = User.objects.get_anonymous_user()
        view = InboxedMessagesView.as_view()

        response = view(request)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(u'/login/'))

    def test_sentmessagesview_as_user(self):
        """
        When called by a user, SentMessagesView should load and context_data be present.
        """
        request = RequestFactory().get('/messages/sent/')
        request.user = self.user
        view = SentMessagesView.as_view()

        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['view'].folder, 'sent')
        self.assertItemsEqual(response.context_data['messages'], [])
        self.assertFalse(response.context_data['is_paginated'])

    def test_sentmessagesview_as_anonymous(self):
        """
        When called by anonymous, SentMessagesView should redirect to login.
        """
        request = RequestFactory().get('/messages/sent/')
        request.user = User.objects.get_anonymous_user()
        view = SentMessagesView.as_view()

        response = view(request)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(u'/login/'))

    def test_archivedmessagesview_as_user(self):
        """
        When called by a user, ArchivedMessagesView should load and context_data be present.
        """
        request = RequestFactory().get('/messages/archive/')
        request.user = self.user
        view = ArchivedMessagesView.as_view()

        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['view'].folder, 'archive')
        self.assertItemsEqual(response.context_data['messages'], [])
        self.assertFalse(response.context_data['is_paginated'])

    def test_archivedmessagesview_as_anonymous(self):
        """
        When called by anonymous, ArchivedMessagesView should redirect to login.
        """
        request = RequestFactory().get('/messages/archive/')
        request.user = User.objects.get_anonymous_user()
        view = ArchivedMessagesView.as_view()

        response = view(request)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(u'/login/'))

    def test_trashedmessagesview_as_user(self):
        """
        When called by a user, TrashedMessagesView should load and context_data be present.
        """
        request = RequestFactory().get('/messages/trash/')
        request.user = self.user
        view = TrashedMessagesView.as_view()

        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['view'].folder, 'trash')
        self.assertItemsEqual(response.context_data['messages'], [])
        self.assertFalse(response.context_data['is_paginated'])

    def test_trashedmessagesview_as_anonymous(self):
        """
        When called by anonymous, TrashedMessagesView should redirect to login.
        """
        request = RequestFactory().get('/messages/trash/')
        request.user = User.objects.get_anonymous_user()
        view = TrashedMessagesView.as_view()

        response = view(request)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(u'/login/'))

    def test_readmessagesview_as_user(self):
        """
        When called by a user, ReadMessagesView should load and context_data be present.
        """
        request = RequestFactory().get('/messages/read/')
        request.user = self.user
        view = ReadMessagesView.as_view()

        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['view'].folder, 'read')
        self.assertItemsEqual(response.context_data['messages'], [])
        self.assertFalse(response.context_data['is_paginated'])

    def test_readmessagesview_as_anonymous(self):
        """
        When called by anonymous, ReadMessagesView should redirect to login.
        """
        request = RequestFactory().get('/messages/read/')
        request.user = User.objects.get_anonymous_user()
        view = ReadMessagesView.as_view()

        response = view(request)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(u'/login/'))

    def test_unreadmessagesview_as_user(self):
        """
        When called by a user, UnreadMessagesView should load and context_data be present.
        """
        request = RequestFactory().get('/messages/unread/')
        request.user = self.user
        view = UnreadMessagesView.as_view()

        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['view'].folder, 'unread')
        self.assertItemsEqual(response.context_data['messages'], [])
        self.assertFalse(response.context_data['is_paginated'])

    def test_unreadmessagesview_as_anonymous(self):
        """
        When called by anonymous, UnreadMessagesView should redirect to login.
        """
        request = RequestFactory().get('/messages/unread/')
        request.user = User.objects.get_anonymous_user()
        view = UnreadMessagesView.as_view()

        response = view(request)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(u'/login/'))


class TestMessageView(TestCase):
    """
    Unit Tests for the MessageView base class.
    """

    def test_messageview_get_queryset(self):
        """
        Test that get_queryset() builds the correct query.
        """
        request = RequestFactory().get('/')
        request.user = Mock()
        view = MessageView()
        view = setup_view(view, request)
        expected_calls = [call.message_set.optimized()]

        view.get_queryset()

        request.user.assert_has_calls(expected_calls)

    @patch('inyoka.privmsg.views.DetailView.get_object')
    def test_messageview_get_object(self, mock_get_object):
        """
        Test that get_object calls mark_read() on the selected message.
        """
        request = RequestFactory().get('/')
        request.user = Mock()
        view = MessageView()
        view = setup_view(view, request)

        view.get_object()

        mock_get_object.assert_has_calls([call(None), call().mark_read()])


class TestMessageViewSubclasses(TestCase):
    """
    Unit tests for the subclasses of MessageView.
    """

    def setUp(self):
        """
        Set up the request object.
        """
        self.request = RequestFactory().get('/')
        self.request.user = User(username='testuser')

    def test_messagetoarchiveview_confirm_action(self):
        """
        Test `confirm_action()` calls `archive()` method on the selected message object.
        """
        view = MessageToArchiveView()
        view = setup_view(view, self.request)
        view.object = Mock()

        view.confirm_action()

        view.object.assert_has_calls([call.archive()])

    def test_messagetotrashview_confirm_action(self):
        """
        Test `confirm_action()` calls `trash()` method on the selected message object.
        """
        view = MessageToTrashView()
        view = setup_view(view, self.request)
        view.object = Mock()

        view.confirm_action()

        view.object.assert_has_calls([call.trash()])

    def test_messagerestoreview_confirm_action(self):
        """
        Test `confirm_action()` calls `restore()` method on the selected message object.
        """
        view = MessageRestoreView()
        view = setup_view(view, self.request)
        view.object = Mock()

        view.confirm_action()

        view.object.assert_has_calls([call.restore()])

    def test_messagerestoreview_get_success_url(self):
        """
        Test `get_success_url()` returns the message's folder url by calling the right method.
        """
        view = MessageRestoreView()
        view = setup_view(view, self.request)
        view.object = Mock()

        view.get_success_url()

        view.object.assert_has_calls([call.get_absolute_url(action='folder')])

    def test_messagedeleteview_confirm_action(self):
        """
        Test `confirm_action()` calls `delete()` method on the selected message object.
        """
        view = MessageDeleteView()
        view = setup_view(view, self.request)
        view.object = Mock()

        view.confirm_action()

        view.object.assert_has_calls([call.delete()])


class TestMessageViewIntegration(TestCase):
    """
    Integration test of the Message views.
    """
    # TODO: write the tests.


class TestBaseMessageComposeView(TestCase):
    """
    Unit Tests for the MessageComposeView class.
    """
    urls = 'inyoka.portal.urls'

    def setUp(self):
        self.request = RequestFactory().get('/')
        self.user = Mock()
        self.view = BaseMessageComposeView()
        self.view.request = self.request
        self.view.request.user = self.user

    def test_get_form_class_normal_user(self):
        """
        Test `get_form_class()` returns MessageComposeForm for normal user.
        """
        self.view.request.user.can.return_value = False
        expected_value = MessageComposeForm

        actual_value = self.view.get_form_class()

        self.assertEqual(actual_value, expected_value)

    def test_get_form_class_privileged_user(self):
        """
        Test `get_form_class()` returns MessageComposeForm for privileged user.
        """
        self.view.request.user.can.return_value = True
        expected_value = PrivilegedMessageComposeForm

        actual_value = self.view.get_form_class()

        self.assertEqual(actual_value, expected_value)

    @patch('inyoka.privmsg.views.CreateView.get_form_kwargs')
    def test_get_form_kwargs(self, mock_get_form_kwargs):
        """
        Test `get_form_kwargs()` adds user to returned dict.
        """
        mock_get_form_kwargs.return_value = {}

        actual_value = self.view.get_form_kwargs()

        self.assertEqual(actual_value['user'], self.view.request.user)

    @patch('inyoka.privmsg.views.MessageData.send')
    @patch('inyoka.privmsg.views.messages.success')
    def test_form_valid(self, mock_success, mock_send):
        """
        Test `form_valid()` calls `MessageData.send()` and adds a flash message.
        """
        expected_author = User(username='testuser')
        expected_subject = 'Subject'
        expected_text = 'Text'
        expected_recipients = [User(username='testuser2')]
        form = MessageComposeForm(user=expected_author)
        form.cleaned_data = {
            'recipients': expected_recipients,
            'subject': expected_subject,
            'text': expected_text,
        }
        self.view.request.user = expected_author

        self.view.form_valid(form)

        mock_success.assert_called_once_with(self.request, _(u'Your message has been sent.'))
        mock_send.assert_called_once_with(
            author=expected_author,
            recipients=expected_recipients,
            subject=expected_subject,
            text=expected_text,
        )

    @patch('inyoka.privmsg.views.MessageData')
    def test_preview_method(self, mock_messagedata):
        text = 'test text'
        self.view.preview_method(text)
        mock_messagedata.assert_has_calls([call.get_text_rendered(text)])

    @patch('inyoka.privmsg.views.BaseMessageComposeView.get_text')
    @patch('inyoka.privmsg.views.BaseMessageComposeView.get_subject')
    @patch('inyoka.privmsg.views.BaseMessageComposeView.get_recipients')
    def test_get_initial(self, mock_recipients, mock_subject, mock_text):
        """
        Test that `get_initial()` returns the correct dict.
        """
        expected_recipients = ''
        expected_subject = ''
        expected_text = ''
        mock_recipients.return_value = expected_recipients
        mock_subject.return_value = expected_subject
        mock_text.return_value = expected_text
        expected_value = {
            'recipients': expected_recipients,
            'subject': expected_subject,
            'text': expected_text,
        }

        actual_value = self.view.get_initial()

        self.assertDictEqual(actual_value, expected_value)

    def test_get_recipients(self):
        """
        Test `get_recipients()`, this method is supposed to be implemented by subclasses.
        """
        self.assertEqual(self.view.get_recipients(), '')

    def test_get_subject(self):
        """
        Test `get_subject()`, this method is supposed to be implemented by subclasses.
        """
        self.assertEqual(self.view.get_subject(), '')

    def test_get_text(self):
        """
        Test `get_text()`, this method is supposed to be implemented by subclasses.
        """
        self.assertEqual(self.view.get_text(), '')


class TestMessageComposeView(TestCase):
    """
    Unit Tests for `MessageComposeView`.
    """

    def setUp(self):
        self.request = RequestFactory().get('/')
        self.user = Mock()
        self.view = MessageComposeView()
        self.view.request = self.request
        self.view.request.user = self.user

    def test_get_recipients_without_user_in_url(self):
        """
        Test `get_recipients()` returns an empty string when called.
        """
        self.view.kwargs = {}
        expected_value = ''
        actual_value = self.view.get_recipients()
        self.assertEqual(actual_value, expected_value)

    def test_get_recipients_with_user_in_url(self):
        """
        Test `get_recipients()` returns the username given in the URL.
        """
        expected_value = 'testuser'
        self.view.kwargs = {'user': expected_value}
        actual_value = self.view.get_recipients()
        self.assertEqual(actual_value, expected_value)


class TestMessageForwardView(TestCase):
    """
    Unit Tests for `MessageForwardView`.
    """

    def setUp(self):
        self.request = RequestFactory().get('/')
        self.user = Mock()
        self.view = MessageForwardView()
        self.view.request = self.request
        self.view.request.user = self.user

    def test_get_queryset(self):
        """
        Test that `get_queryset()` returns the correct QuerySet with the users messages.
        """
        expected_calls = [call.message_set.optimized()]
        self.view.get_queryset()
        self.request.user.assert_has_calls(expected_calls)

    def test_get_subject(self):
        """
        Test that `get_subject()` prefixes the forwarded message's subject with 'Fw: '
        """
        dummy_subject = 'testsubject'
        expected_value = 'Fw: testsubject'
        self.view.object = Mock(subject=dummy_subject)

        actual_value = self.view.get_subject()

        self.assertEqual(actual_value, expected_value)

    def test_get_subject_already_forwarded(self):
        """
        Test that `get_subject()` does not change the subject, when it is already prefixed.
        """
        expected_value = 'Fw: testsubject'
        self.view.object = Mock(subject=expected_value)

        actual_value = self.view.get_subject()

        self.assertEqual(actual_value, expected_value)

    @patch('inyoka.privmsg.views.quote_text')
    def test_get_text(self, mock_quote_text):
        """
        Test that `get_text()` calls `quote_text()` with the correct parameters.
        """
        expected_text = 'test text'
        expected_user = User(username='testuser')
        self.view.object = Mock(text=expected_text, author=expected_user)

        self.view.get_text()

        mock_quote_text.assert_called_once_with(
            text=expected_text,
            author=expected_user
        )


class TestMessageReplyView(TestCase):
    def setUp(self):
        self.request = RequestFactory().get('/')
        self.user = Mock()
        self.view = MessageReplyView()
        self.view.request = self.request
        self.view.request.user = self.user

    def test_messagereplyview_get_queryset(self):
        """
        Test that get_queryset() builds the correct query.
        """
        request = RequestFactory().get('/')
        request.user = Mock()
        view = MessageReplyView()
        view = setup_view(view, request)
        expected_calls = [call.message_set.optimized()]

        view.get_queryset()

        request.user.assert_has_calls(expected_calls)

    def test_get_recipients(self):
        expected_value = 'testuser'
        self.view.object = Mock(author=User(pk=1, username=expected_value))

        actual_value = self.view.get_recipients()

        self.assertEqual(actual_value, expected_value)

    def test_get_recipients_reply_to_all(self):
        self.view.reply_to_all = True
        self.view.request.user = User(pk=1, username='testuser')
        author = User(pk=2, username='author')
        recipients = [
            User(pk=3, username='recipient'),
        ]
        self.view.object = Mock(
            author=author,
            recipients=recipients,
        )
        expected_value = 'author;recipient'

        actual_value = self.view.get_recipients()

        self.assertEqual(actual_value, expected_value)

    def test_get_recipients_reply_to_all_with_viewer_in_recipients(self):
        self.view.reply_to_all = True
        self.view.request.user = User(pk=1, username='testuser')
        author = User(pk=2, username='author')
        recipients = [
            User(pk=3, username='recipient'),
            self.view.request.user,
        ]
        self.view.object = Mock(
            author=author,
            recipients=recipients,
        )
        expected_value = 'author;recipient'

        actual_value = self.view.get_recipients()

        self.assertEqual(actual_value, expected_value)

    def test_get_subject(self):
        dummy_subject = 'testsubject'
        expected_value = 'Re: testsubject'
        self.view.object = Mock(subject=dummy_subject)

        actual_value = self.view.get_subject()

        self.assertEqual(actual_value, expected_value)

    def test_get_subject_already_replied(self):
        expected_value = 'Re: testsubject'
        self.view.object = Mock(subject=expected_value)

        actual_value = self.view.get_subject()

        self.assertEqual(actual_value, expected_value)

    @patch('inyoka.privmsg.views.quote_text')
    def test_get_text(self, mock_quote_text):
        expected_text = 'test text'
        expected_user = User(username='testuser')
        self.view.object = Mock(author=expected_user, text=expected_text)

        self.view.get_text()

        mock_quote_text.assert_called_once_with(
            text=expected_text,
            author=expected_user
        )


class TestMessageReplyReportedTopicView(TestCase):
    def setUp(self):
        self.request = RequestFactory().get('/')
        self.user = Mock()
        self.view = MessageReplyReportedTopicView()
        self.view.request = self.request
        self.view.request.user = self.user

    @patch('inyoka.privmsg.views.User')
    def test_get_recipients(self, mock_user):
        expected_value = 'testuser'
        self.view.object = Mock()
        mock_user.objects.get.return_value = User(username=expected_value)

        actual_value = self.view.get_recipients()

        self.assertEqual(actual_value, expected_value)

    def test_get_subject(self):
        dummy_subject = 'testsubject'
        expected_value = 'Re: testsubject'
        self.view.object = Mock(title=dummy_subject)

        actual_value = self.view.get_subject()

        self.assertEqual(actual_value, expected_value)

    @patch('inyoka.privmsg.views.quote_text')
    def test_get_text(self, mock_quote_text):
        expected_text = 'test text'
        expected_user = User(username='testuser')
        self.view.object = Mock(author=expected_user, reported=expected_text)

        self.view.get_text()

        mock_quote_text.assert_called_once_with(
            text=expected_text,
            author=expected_user
        )


class TestMessageReplySuggestedArticleView(TestCase):
    def setUp(self):
        self.request = RequestFactory().get('/')
        self.user = Mock()
        self.view = MessageReplySuggestedArticleView()
        self.view.request = self.request
        self.view.request.user = self.user

    def test_get_recipients(self):
        expected_value = 'testuser'
        self.view.object = Mock(author=User(username=expected_value))

        actual_value = self.view.get_recipients()

        self.assertEqual(actual_value, expected_value)

    def test_get_subject(self):
        dummy_subject = 'testsubject'
        expected_value = 'Re: testsubject'
        self.view.object = Mock(title=dummy_subject)

        actual_value = self.view.get_subject()

        self.assertEqual(actual_value, expected_value)

    @patch('inyoka.privmsg.views.quote_text')
    def test_get_text(self, mock_quote_text):
        expected_intro = 'intro'
        expected_text = 'test text'
        expected_user = User(username='testuser')
        expected_value = '{}\n\n{}'.format(expected_intro, expected_text)
        self.view.object = Mock(
            author=expected_user,
            intro=expected_intro,
            text=expected_text
        )

        self.view.get_text()

        mock_quote_text.assert_called_once_with(
            text=expected_value,
            author=expected_user
        )


class TestMultiMessageProcessView(TestCase):
    """
    Unit Tests for `MultiMessageProcessView`.
    """

    def setUp(self):
        self.request = RequestFactory().get('/')
        self.user = Mock()
        self.view = MultiMessageProcessView()
        self.view.request = self.request
        self.view.request.user = self.user

    @patch('inyoka.privmsg.views.FormMixin.get_form_kwargs')
    def test_get_form_kwargs(self, mock_get_form_kwargs):
        """
        Test `get_form_kwargs()` returns a dict containing the queryset.
        """
        expected_value = 'queryset'
        mock_get_form_kwargs.return_value = {}
        self.view.get_queryset = Mock(return_value=expected_value)

        actual_value = self.view.get_form_kwargs()

        self.assertEqual(actual_value['queryset'], expected_value)

    def test_get_queryset(self):
        """
        Test the `get_queryset()` method.
        """
        expected_value = 'Faked'
        self.view.request.user.message_set = expected_value

        actual_value = self.view.get_queryset()

        self.assertEqual(actual_value, expected_value)

    def test_post_when_form_is_valid(self):
        """
        Test `post()` method calls `form_valid()` when form successfully validates.
        """
        mock_form = Mock()
        mock_form.is_valid = Mock(return_value=True)
        mock_get_form = Mock(return_value=mock_form)
        self.view.get_form = mock_get_form
        self.view.form_valid = Mock(return_value=True)

        self.view.post(self.request)

        self.view.form_valid.called_once_with(self.view.get_form)

    def test_post_when_form_is_invalid(self):
        """
        Test `post()` raises a 404 error when form is not valid.
        """
        mock_form = Mock()
        mock_form.is_valid = Mock(return_value=False)
        mock_get_form = Mock(return_value=mock_form)
        self.view.get_form = mock_get_form

        with self.assertRaises(Http404):
            self.view.post(self.request)

    @patch('inyoka.privmsg.views.HttpResponseRedirect')
    def test_form_valid_with_action_archive(self, mock_redirect):
        """
        Test `form_valid()` calls `bulk_archive()` on the filtered queryset (when called with action "archive").
        """
        mocked_queryset = Mock()
        form = MultiMessageSelectForm(queryset=mocked_queryset)
        form.cleaned_data = {
            'selected_messages': mocked_queryset,
            'action': 'archive',
        }

        self.view.form_valid(form)

        mocked_queryset.assert_has_calls([call.bulk_archive()])
        self.request.user.assert_has_calls([call.privmsg_count.db_count(write_cache=True)])
        mock_redirect.assert_called_once_with(reverse_lazy('privmsg-archive'))

    @patch('inyoka.privmsg.views.HttpResponseRedirect')
    def test_form_valid_with_action_trash(self, mock_redirect):
        """
        Test `form_valid()` calls `bulk_trash()` on the filtered queryset (when called with action "trash").
        """
        mocked_queryset = Mock()
        form = MultiMessageSelectForm(queryset=mocked_queryset)
        form.cleaned_data = {
            'selected_messages': mocked_queryset,
            'action': 'trash',
        }

        self.view.form_valid(form)

        mocked_queryset.assert_has_calls([call.bulk_trash()])
        self.request.user.assert_has_calls([call.privmsg_count.db_count(write_cache=True)])
        mock_redirect.assert_called_once_with(reverse_lazy('privmsg-trash'))

    @patch('inyoka.privmsg.views.HttpResponseRedirect')
    def test_form_valid_with_action_restore(self, mock_redirect):
        """
        Test `form_valid()` calls `bulk_restore()` on the filtered queryset (when called with action "restore").
        """
        mocked_queryset = Mock()
        form = MultiMessageSelectForm(queryset=mocked_queryset)
        form.cleaned_data = {
            'selected_messages': mocked_queryset,
            'action': 'restore',
        }

        self.view.form_valid(form)

        mocked_queryset.assert_has_calls([call.bulk_restore()])
        mock_redirect.assert_called_once_with(reverse_lazy('privmsg-inbox'))
