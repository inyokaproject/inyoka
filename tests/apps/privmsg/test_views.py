# -*- coding: utf-8 -*-
"""
    tests.apps.privmsg.test_views
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test privmsg views.

    :copyright: (c) 2011-2016 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse, reverse_lazy
from django.http import Http404
from django.test import RequestFactory
from django.utils.translation import ugettext as _
from inyoka.ikhaya.models import Suggestion
from inyoka.forum.models import Forum, Topic
from inyoka.portal.user import User, PERMISSION_MAPPING
from inyoka.privmsg.forms import (
    MessageComposeForm,
    MultiMessageSelectForm,
    PrivilegedMessageComposeForm,
)
from inyoka.privmsg.models import MessageData
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
from mock import call, Mock, patch


def setup_view(view, request, *args, **kwargs):
    """Mimic as_view() but returns a view instance."""
    view.request = request
    view.args = args
    view.kwargs = kwargs
    return view


def request_factory(request_path="/", request_user=None, request_method="GET", request_data={}):
        """Build a request object, this is a wrapper for Django's `RequestFactory`."""
        if request_user is None:
            request_user = User.get_anonymous_user()

        if request_method == 'POST':
            request = RequestFactory().post(request_path, request_data)
        else:
            request = RequestFactory().get(request_path, request_data)

        request.user = request_user
        setattr(request, 'session', 'session')
        setattr(request, '_messages', Mock())

        return request


class TestMessagesFolderView(TestCase):
    """Unit Tests for the MessagesFolderView base class."""

    def test_get_queryset_builds_correct_queryset(self):
        """Test that get_queryset() builds the correct queryset."""
        request = RequestFactory().get('/')
        request.user = Mock()
        view = MessagesFolderView(queryset_name='fake')
        view = setup_view(view, request)
        expected_calls = [call.message_set.fake(), call.message_set.fake().optimized()]

        view.get_queryset()

        request.user.assert_has_calls(expected_calls)

    def test_get_queryset_without_queryset_name(self):
        """Test that get_queryset() raises `ImproperlyConfigured` when `queryset_name` is not set."""
        request = RequestFactory().get('/')
        request.user = Mock()
        view = MessagesFolderView()
        view = setup_view(view, request)

        with self.assertRaises(ImproperlyConfigured):
            view.get_queryset()


class TestFolderMessagesViewIntegration(TestCase):
    """Integration Test for subclasses of `MessagesFolderView`."""

    urls = 'inyoka.portal.urls'

    def setUp(self):
        """Set up a user to test with."""
        self.user = User.objects.register_user(
            username='testuser',
            email='testuser',
            password='testuser',
            send_mail=False,
        )

    def test_inboxedmessagesview_as_user(self):
        """When called by a user, InboxedMessagesView should load and context_data be present."""
        request = RequestFactory().get(reverse_lazy('privmsg-inbox'))
        request.user = self.user
        view = InboxedMessagesView.as_view()

        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['view'].folder, 'inbox')
        self.assertItemsEqual(response.context_data['messages'], [])
        self.assertFalse(response.context_data['is_paginated'])

    def test_inboxedmessagesview_as_anonymous_redirects_to_login(self):
        """When called by anonymous, InboxedMessagesView should redirect to login."""
        request = RequestFactory().get(reverse_lazy('privmsg-inbox'))
        request.user = User.objects.get_anonymous_user()
        view = InboxedMessagesView.as_view()

        response = view(request)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(u'/login/'))

    def test_sentmessagesview_as_user(self):
        """When called by a user, SentMessagesView should load and context_data be present."""
        request = RequestFactory().get(reverse_lazy('privmsg-sent'))
        request.user = self.user
        view = SentMessagesView.as_view()

        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['view'].folder, 'sent')
        self.assertItemsEqual(response.context_data['messages'], [])
        self.assertFalse(response.context_data['is_paginated'])

    def test_sentmessagesview_as_anonymous_redirects_to_login(self):
        """When called by anonymous, SentMessagesView should redirect to login."""
        request = RequestFactory().get(reverse_lazy('privmsg-sent'))
        request.user = User.objects.get_anonymous_user()
        view = SentMessagesView.as_view()

        response = view(request)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(u'/login/'))

    def test_archivedmessagesview_as_user(self):
        """When called by a user, ArchivedMessagesView should load and context_data be present."""
        request = RequestFactory().get(reverse_lazy('privmsg-archive'))
        request.user = self.user
        view = ArchivedMessagesView.as_view()

        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['view'].folder, 'archive')
        self.assertItemsEqual(response.context_data['messages'], [])
        self.assertFalse(response.context_data['is_paginated'])

    def test_archivedmessagesview_as_anonymous_redirects_to_login(self):
        """When called by anonymous, ArchivedMessagesView should redirect to login."""
        request = RequestFactory().get(reverse_lazy('privmsg-archive'))
        request.user = User.objects.get_anonymous_user()
        view = ArchivedMessagesView.as_view()

        response = view(request)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(u'/login/'))

    def test_trashedmessagesview_as_user(self):
        """When called by a user, TrashedMessagesView should load and context_data be present."""
        request = RequestFactory().get(reverse_lazy('privmsg-trash'))
        request.user = self.user
        view = TrashedMessagesView.as_view()

        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['view'].folder, 'trash')
        self.assertItemsEqual(response.context_data['messages'], [])
        self.assertFalse(response.context_data['is_paginated'])

    def test_trashedmessagesview_as_anonymous_redirects_to_login(self):
        """When called by anonymous, TrashedMessagesView should redirect to login."""
        request = RequestFactory().get(reverse_lazy('privmsg-trash'))
        request.user = User.objects.get_anonymous_user()
        view = TrashedMessagesView.as_view()

        response = view(request)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(u'/login/'))

    def test_readmessagesview_as_user(self):
        """When called by a user, ReadMessagesView should load and context_data be present."""
        request = RequestFactory().get(reverse_lazy('privmsg-read'))
        request.user = self.user
        view = ReadMessagesView.as_view()

        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['view'].folder, 'read')
        self.assertItemsEqual(response.context_data['messages'], [])
        self.assertFalse(response.context_data['is_paginated'])

    def test_readmessagesview_as_anonymous_redirects_to_login(self):
        """When called by anonymous, ReadMessagesView should redirect to login."""
        request = RequestFactory().get(reverse_lazy('privmsg-read'))
        request.user = User.objects.get_anonymous_user()
        view = ReadMessagesView.as_view()

        response = view(request)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(u'/login/'))

    def test_unreadmessagesview_as_user(self):
        """When called by a user, UnreadMessagesView should load and context_data be present."""
        request = RequestFactory().get(reverse_lazy('privmsg-unread'))
        request.user = self.user
        view = UnreadMessagesView.as_view()

        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['view'].folder, 'unread')
        self.assertItemsEqual(response.context_data['messages'], [])
        self.assertFalse(response.context_data['is_paginated'])

    def test_unreadmessagesview_as_anonymous_redirects_to_login(self):
        """When called by anonymous, UnreadMessagesView should redirect to login."""
        request = RequestFactory().get(reverse_lazy('privmsg-unread'))
        request.user = User.objects.get_anonymous_user()
        view = UnreadMessagesView.as_view()

        response = view(request)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(u'/login/'))


class TestMessageView(TestCase):
    """Unit Tests for the `MessageView` base class."""

    def setUp(self):
        """Set up the view for testing."""
        self.request = RequestFactory().get('/')
        self.request.user = Mock()
        self.view = MessageView()
        self.view = setup_view(self.view, self.request)

    def test_get_queryset(self):
        """Test that `get_queryset()` builds the correct query."""
        expected_calls = [call.message_set.optimized()]
        self.view.get_queryset()
        self.request.user.assert_has_calls(expected_calls)

    @patch('inyoka.privmsg.views.DetailView.get_object')
    def test_get_object(self, mock_get_object):
        """Test that `get_object()` calls `mark_read()` on the selected message."""
        self.view.get_object()
        mock_get_object.assert_has_calls([call(None), call().mark_read()])


class TestMessageViewSubclasses(TestCase):
    """Unit tests for the subclasses of `MessageView`."""

    def setUp(self):
        """Set up the request object."""
        self.request = RequestFactory().get('/')
        self.request.user = User(username='testuser')

    def test_messagetoarchiveview_confirm_action(self):
        """Test `confirm_action()` calls `archive()` method on the selected message object."""
        view = MessageToArchiveView()
        view = setup_view(view, self.request)
        view.object = Mock()

        view.confirm_action()

        view.object.assert_has_calls([call.archive()])

    def test_messagetotrashview_confirm_action(self):
        """Test `confirm_action()` calls `trash()` method on the selected message object."""
        view = MessageToTrashView()
        view = setup_view(view, self.request)
        view.object = Mock()

        view.confirm_action()

        view.object.assert_has_calls([call.trash()])

    def test_messagerestoreview_confirm_action(self):
        """Test `confirm_action()` calls `restore()` method on the selected message object."""
        view = MessageRestoreView()
        view = setup_view(view, self.request)
        view.object = Mock()

        view.confirm_action()

        view.object.assert_has_calls([call.restore()])

    def test_messagerestoreview_get_success_url(self):
        """Test `get_success_url()` returns the message's folder url by calling the right method."""
        view = MessageRestoreView()
        view = setup_view(view, self.request)
        view.object = Mock()

        view.get_success_url()

        view.object.assert_has_calls([call.get_absolute_url(action='folder')])

    def test_messagedeleteview_confirm_action(self):
        """Test `confirm_action()` calls `delete()` method on the selected message object."""
        view = MessageDeleteView()
        view = setup_view(view, self.request)
        view.object = Mock()

        view.confirm_action()

        view.object.assert_has_calls([call.delete()])


class TestMessageViewIntegration(TestCase):
    """Integration test of the Message views."""

    urls = 'inyoka.portal.urls'

    def setUp(self):
        """Set up a user to test with."""
        self.author = User.objects.register_user(
            username='testuser',
            email='testuser',
            password='testuser',
            send_mail=False,
        )
        self.recipient = User.objects.register_user(
            username='testuser2',
            email='testuser2',
            password='testuser2',
            send_mail=False,
        )
        MessageData.send(
            author=self.author,
            recipients=[self.recipient],
            subject='testsubject',
            text='testmessage',
        )
        self.message = self.author.message_set.sent().first()

    def test_messageview_as_user(self):
        """`MessageView` should display the message, if called by the recipient."""
        request = RequestFactory().get(reverse_lazy('privmsg-message', args=(self.message.pk,)))
        request.user = self.author
        view = MessageView.as_view()

        response = view(request, pk=self.message.pk)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['message'].text, self.message.text)

    def test_messageview_as_invalid_user(self):
        """`MessageView` should give a 404 with a message_id the user has no access to."""
        request = RequestFactory().get(reverse_lazy('privmsg-message', args=(self.message.pk,)))
        request.user = self.recipient
        view = MessageView.as_view()

        with self.assertRaises(Http404):
            view(request, pk=self.message.pk)

    def test_messageview_as_anonymous_redirects_to_login(self):
        """When called by anonymous, `MessageView` should redirect to login."""
        request = RequestFactory().get(reverse_lazy('privmsg-message', args=(self.message.pk,)))
        request.user = User.objects.get_anonymous_user()
        view = MessageView.as_view()

        response = view(request, pk=self.message.pk)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(u'/login/'))


class TestMessageViewSubclassesIntegration(TestCase):
    """Integration Tests for `MessageView` subclasses (e.g. `MessageToArchiveView`)."""

    def setUp(self):
        """Set up testing users and messages."""
        self.author = User.objects.register_user(
            username='author',
            email='author',
            password='',
            send_mail=False,
        )
        self.recipient = User.objects.register_user(
            username='recipient',
            email='recipient',
            password='',
            send_mail=False,
        )
        MessageData.send(
            author=self.author,
            recipients=[self.recipient],
            subject='testsubject',
            text='some text',
        )
        self.sent_message = self.author.message_set.sent().first()
        self.received_message = self.recipient.message_set.inboxed().first()

    # Note: since these are derived from `MessageView` we don't need to test access as anonymous.
    def test_messagetoarchiveview_confirmed(self):
        """Test that `MessageToArchiveView` archives the message and redirects to the archive."""
        view = MessageToArchiveView.as_view()
        request = request_factory(
            request_path=reverse_lazy('privmsg-message-archive', args=(self.sent_message.pk,)),
            request_user=self.author,
            request_method='POST',
            request_data={'confirm': 'Confirm'},
        )

        response = view(request, pk=self.sent_message.pk)
        self.sent_message.refresh_from_db()

        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse_lazy('privmsg-archive'), response.url)
        self.assertEqual('archive', self.sent_message.folder)

    def test_messagetoarchiveview_cancelled(self):
        """Test that `MessageToArchiveView` redirects to the message without archiving it."""
        view = MessageToArchiveView.as_view()
        request = request_factory(
            request_path=reverse_lazy('privmsg-message-archive', args=(self.sent_message.pk,)),
            request_user=self.author,
            request_method='POST',
            request_data={'cancel': 'Cancel'},
        )

        response = view(request, pk=self.sent_message.pk)
        self.sent_message.refresh_from_db()

        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse_lazy('privmsg-message', args=(self.sent_message.pk,)), response.url)
        self.assertEqual(u'sent', self.sent_message.folder)

    def test_messagetotrashview_confirmed(self):
        """Test that `MessageToTrashView` moves the message to trash and redirects to trash."""
        view = MessageToTrashView.as_view()
        request = request_factory(
            request_path=reverse_lazy('privmsg-message-trash', args=(self.sent_message.pk,)),
            request_user=self.author,
            request_method='POST',
            request_data={'confirm': 'Confirm'},
        )

        response = view(request, pk=self.sent_message.pk)
        self.sent_message.refresh_from_db()

        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse_lazy('privmsg-trash'), response.url)
        self.assertEqual(u'trash', self.sent_message.folder)

    def test_messagetotrashview_cancelled(self):
        """Test that `MessageToTrashView` redirects to the message without trashing it."""
        view = MessageToTrashView.as_view()
        request = request_factory(
            request_path=reverse_lazy('privmsg-message-trash', args=(self.sent_message.pk,)),
            request_user=self.author,
            request_method='POST',
            request_data={'cancel': 'Cancel'},
        )

        response = view(request, pk=self.sent_message.pk)
        self.sent_message.refresh_from_db()

        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse_lazy('privmsg-message', args=(self.sent_message.pk,)), response.url)
        self.assertEqual(u'sent', self.sent_message.folder)

    def test_messagerestoreview_confirmed_with_received_message(self):
        """Test that `MessageRestoreView` restores a received message and redirects to inbox."""
        self.received_message.archive()
        view = MessageRestoreView.as_view()
        request = request_factory(
            request_path=reverse_lazy('privmsg-message-restore', args=(self.received_message.pk,)),
            request_user=self.recipient,
            request_method='POST',
            request_data={'confirm': 'Confirm'},
        )

        response = view(request, pk=self.received_message.pk)
        self.received_message.refresh_from_db()

        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse_lazy('privmsg-inbox'), response.url)
        self.assertEqual('inbox', self.received_message.folder)

    def test_messagerestoreview_confirmed_with_sent_message(self):
        """Test that `MessageRestoreView` archives a sent message and redirects to sent."""
        self.sent_message.archive()
        view = MessageRestoreView.as_view()
        request = request_factory(
            request_path=reverse_lazy('privmsg-message-restore', args=(self.sent_message.pk,)),
            request_user=self.author,
            request_method='POST',
            request_data={'confirm': 'Confirm'},
        )

        response = view(request, pk=self.sent_message.pk)
        self.sent_message.refresh_from_db()

        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse_lazy('privmsg-sent'), response.url)
        self.assertEqual('sent', self.sent_message.folder)

    def test_messagerestoreview_cancelled(self):
        """Test that `MessageRestoreView` redirects to the message without restoring it."""
        self.sent_message.archive()
        view = MessageRestoreView.as_view()
        request = request_factory(
            request_path=reverse_lazy('privmsg-message-restore', args=(self.sent_message.pk,)),
            request_user=self.author,
            request_method='POST',
            request_data={'cancel': 'Cancel'},
        )

        response = view(request, pk=self.sent_message.pk)
        self.sent_message.refresh_from_db()

        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse_lazy('privmsg-message', args=(self.sent_message.pk,)), response.url)
        self.assertEqual('archive', self.sent_message.folder)

    def test_messagedeleteview_confirmed(self):
        """Test that `MessageDeleteView` deletes the message and redirects to inbox."""
        view = MessageDeleteView.as_view()
        request = request_factory(
            request_path=reverse_lazy('privmsg-message-delete', args=(self.sent_message.pk,)),
            request_user=self.author,
            request_method='POST',
            request_data={'confirm': 'Confirm'},
        )

        response = view(request, pk=self.sent_message.pk)

        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse_lazy('privmsg-inbox'), response.url)
        self.assertFalse(self.author.message_set.sent().exists())

    def test_messagedeleteview_cancelled(self):
        """Test that `MessageDeleteView` redirects to the message without deleting it."""
        view = MessageDeleteView.as_view()
        request = request_factory(
            request_path=reverse_lazy('privmsg-message-delete', args=(self.sent_message.pk,)),
            request_user=self.author,
            request_method='POST',
            request_data={'cancel': 'Cancel'},
        )

        response = view(request, pk=self.sent_message.pk)
        self.sent_message.refresh_from_db()

        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse_lazy('privmsg-message', args=(self.sent_message.pk,)), response.url)
        self.assertEqual('sent', self.sent_message.folder)


class TestBaseMessageComposeView(TestCase):
    """Unit Tests for the MessageComposeView class."""
    urls = 'inyoka.portal.urls'

    def setUp(self):
        """Set up the view for testing."""
        self.request = RequestFactory().get('/')
        self.user = Mock()
        self.view = BaseMessageComposeView()
        self.view.request = self.request
        self.view.request.user = self.user

    def test_get_form_class_normal_user(self):
        """Test `get_form_class()` returns MessageComposeForm for normal user."""
        self.view.request.user.can.return_value = False
        expected_value = MessageComposeForm

        actual_value = self.view.get_form_class()

        self.assertEqual(actual_value, expected_value)

    def test_get_form_class_privileged_user(self):
        """Test `get_form_class()` returns MessageComposeForm for privileged user."""
        self.view.request.user.can.return_value = True
        expected_value = PrivilegedMessageComposeForm

        actual_value = self.view.get_form_class()

        self.assertEqual(actual_value, expected_value)

    @patch('inyoka.privmsg.views.FormView.get_form_kwargs')
    def test_get_form_kwargs(self, mock_get_form_kwargs):
        """Test `get_form_kwargs()` adds user to returned dict."""
        mock_get_form_kwargs.return_value = {}

        actual_value = self.view.get_form_kwargs()

        self.assertEqual(actual_value['user'], self.view.request.user)

    @patch('inyoka.privmsg.views.MessageData.send')
    @patch('inyoka.privmsg.views.messages.success')
    def test_form_valid(self, mock_success, mock_send):
        """Test `form_valid()` calls `MessageData.send()` and adds a flash message."""
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
        """Test that `get_initial()` returns the correct dict."""
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

    def test_get_object(self):
        """Test `get_object()`, this method is supposed to be implemented by subclasses."""
        self.assertEqual(self.view.get_object(), None)

    def test_get_recipients(self):
        """Test `get_recipients()`, this method is supposed to be implemented by subclasses."""
        self.assertEqual(self.view.get_recipients(), '')

    def test_get_subject(self):
        """Test `get_subject()`, this method is supposed to be implemented by subclasses."""
        self.assertEqual(self.view.get_subject(), '')

    def test_get_text(self):
        """Test `get_text()`, this method is supposed to be implemented by subclasses."""
        self.assertEqual(self.view.get_text(), '')


class TestMessageComposeView(TestCase):
    """Unit Tests for `MessageComposeView`."""

    def setUp(self):
        """Set up the view for testing."""
        self.request = RequestFactory().get('/')
        self.user = Mock()
        self.view = MessageComposeView()
        self.view.request = self.request
        self.view.request.user = self.user

    def test_get_recipients_without_user_in_url(self):
        """Test `get_recipients()` returns an empty string when called."""
        self.view.kwargs = {}
        expected_value = ''
        actual_value = self.view.get_recipients()
        self.assertEqual(actual_value, expected_value)

    def test_get_recipients_with_user_in_url(self):
        """Test `get_recipients()` returns the username given in the URL."""
        expected_value = 'testuser'
        self.view.kwargs = {'user': expected_value}
        actual_value = self.view.get_recipients()
        self.assertEqual(actual_value, expected_value)


class TestMessageComposeViewIntegration(TestCase):
    """Integration Tests for `MessageComposeView`."""

    def setUp(self):
        """Set up users to test with."""
        self.author = User.objects.register_user(
            username='author',
            email='author',
            password='author',
            send_mail=False,
        )
        self.privileged_author = User.objects.register_user(
            username='pauthor',
            email='pauthor',
            password='pauthor',
            send_mail=False,
        )
        self.privileged_author._permissions = PERMISSION_MAPPING['send_group_pm']  # TODO: new permissions
        self.privileged_author.save()
        self.recipient = User.objects.register_user(
            username='recipient',
            email='recipient',
            password='recipient',
            send_mail=False,
        )
        self.client.login(username='author', password='author')

    def test_messagecomposeview_get(self):
        """Test that calling privmsg-compose as user returns the form."""
        url = reverse_lazy('privmsg-compose')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(isinstance(response.context_data['form'], MessageComposeForm))

    def test_messagecomposeview_get_with_user(self):
        """Test that calling privmsg-compose-user with a username returns a pre-filled form."""
        url = reverse_lazy('privmsg-compose-user', args=(self.recipient.username,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.recipient.username, response.context_data['form']['recipients'].value())

    def test_messagecomposeview_get_as_privileged_user(self):
        """Test that calling privmsg-compose as privileged user returns a form with group_recipients field."""
        self.client.logout()
        self.client.login(username='pauthor', password='pauthor')
        url = reverse_lazy('privmsg-compose')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(isinstance(response.context_data['form'], PrivilegedMessageComposeForm))

    def test_messagecomposeview_submit_invalid_form_data(self):
        """Test that submitting with invalid form data shows the form again with error attached."""
        url = reverse_lazy('privmsg-compose')
        data = {
            'recipients': '',
            'subject': '',
            'text': '',
        }
        response = self.client.post(url, data)  # submit the form without filling it out.
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context_data)
        self.assertIn('recipients', response.context_data['form'].errors)
        self.assertIn('subject', response.context_data['form'].errors)
        self.assertIn('text', response.context_data['form'].errors)

    def test_messagecomposeview_submit_with_valid_data(self):
        """Test that submitting with valid data redirects to privmsg-sent and creates the message."""
        url = reverse_lazy('privmsg-compose')
        data = {
            'recipients': self.recipient.username,
            'subject': 'test',
            'text': 'test',
        }
        response = self.client.post(url, data)
        self.assertTrue(response.url.endswith(reverse('privmsg-sent')))
        self.assertEqual(self.author.message_set.sent().count(), 1)
        self.assertEqual(self.recipient.message_set.unread().count(), 1)


class TestMessageForwardView(TestCase):
    """Unit Tests for `MessageForwardView`."""

    def setUp(self):
        """Set up the view for testing."""
        self.request = RequestFactory().get('/')
        self.user = Mock()
        self.view = MessageForwardView()
        self.view.request = self.request
        self.view.request.user = self.user

    def test_get_queryset(self):
        """Test that `get_queryset()` returns the correct QuerySet with the users messages."""
        expected_calls = [call.message_set.optimized()]
        self.view.get_queryset()
        self.request.user.assert_has_calls(expected_calls)

    @patch('inyoka.privmsg.views.MessageForwardView.get_queryset')
    def test_get_object(self, mock_get_queryset):
        """Test that `get_object()` return a `Message` object."""
        expected_pk = 6443
        self.view.kwargs = {'pk': expected_pk}

        self.view.get_object()

        mock_get_queryset.assert_has_calls([call(), call().get(pk=expected_pk)])

    def test_get_subject(self):
        """Test that `get_subject()` prefixes the forwarded message's subject with 'Fw: '."""
        dummy_subject = 'testsubject'
        expected_value = 'Fw: testsubject'
        self.view.object = Mock(subject=dummy_subject)

        actual_value = self.view.get_subject()

        self.assertEqual(actual_value, expected_value)

    def test_get_subject_already_forwarded(self):
        """Test that `get_subject()` does not change the subject, when it is already prefixed."""
        expected_value = 'Fw: testsubject'
        self.view.object = Mock(subject=expected_value)

        actual_value = self.view.get_subject()

        self.assertEqual(actual_value, expected_value)

    @patch('inyoka.privmsg.views.quote_text')
    def test_get_text(self, mock_quote_text):
        """Test that `get_text()` calls `quote_text()` with the correct parameters."""
        expected_text = 'test text'
        expected_user = User(username='testuser')
        self.view.object = Mock(text=expected_text, author=expected_user)

        self.view.get_text()

        mock_quote_text.assert_called_once_with(
            text=expected_text,
            author=expected_user
        )


class TestMessageForwardViewIntegration(TestCase):
    """Integration Tests for `MessageForwardView`."""

    def setUp(self):
        """Set up testing users and messages."""
        self.author = User.objects.register_user(
            username='author',
            email='author',
            password='author',
            send_mail=False,
        )
        self.recipient = User.objects.register_user(
            username='recipient',
            email='recipient',
            password='recipient',
            send_mail=False,
        )
        MessageData.send(
            author=self.author,
            recipients=[self.recipient],
            subject='testsubject',
            text='testmessage',
        )
        self.message = self.author.message_set.sent().first()
        self.other_message = self.recipient.message_set.inboxed().first()
        self.client.login(username='author', password='author')

    def test_messageforwardview_with_invalid_message(self):
        """Test that trying to forward a message not belonging to the user gives a 404."""
        url = reverse('privmsg-message-forward', args=(self.other_message.id,))
        response = self.client.get(url)
        self.assertEqual(404, response.status_code)

    def test_messageforwardview_with_valid_message(self):
        """Test that trying to forward a message returns a pre-filled form."""
        url = reverse('privmsg-message-forward', args=(self.message.id,))
        response = self.client.get(url)
        self.assertIn('form', response.context_data)
        self.assertEqual('Fw: testsubject', response.context_data['form']['subject'].value())
        self.assertIn('> testmessage', response.context_data['form']['text'].value())


class TestMessageReplyView(TestCase):
    """Unit tests for `MessageReplyView`."""

    def setUp(self):
        """Set up the view for testing."""
        self.request = RequestFactory().get('/')
        self.user = Mock()
        self.view = MessageReplyView()
        self.view.kwargs = {}
        self.view.request = self.request
        self.view.request.user = self.user

    def test_get_queryset(self):
        """Test that get_queryset() builds the correct query."""
        request = RequestFactory().get('/')
        request.user = Mock()
        view = MessageReplyView()
        view = setup_view(view, request)
        expected_calls = [call.message_set.optimized()]

        view.get_queryset()

        request.user.assert_has_calls(expected_calls)

    @patch('inyoka.privmsg.views.MessageReplyView.get_queryset')
    def test_get_object(self, mock_get_queryset):
        """Test that `get_object()` returns the message that is being replied to."""
        expected_pk = 6443
        self.view.kwargs = {'pk': expected_pk}

        self.view.get_object()

        mock_get_queryset.assert_has_calls([call(), call().get(pk=expected_pk)])

    def test_get_recipients(self):
        """Test that `get_recipients()` returns the correct recipients."""
        expected_value = 'testuser'
        self.view.object = Mock(author=User(pk=1, username=expected_value))

        actual_value = self.view.get_recipients()

        self.assertEqual(actual_value, expected_value)

    def test_get_recipients_reply_to_all(self):
        """Test that `get_recipients()` returns the correct recipients when replying to all."""
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
        """Test that `get_recipients()` omits the current user when replying to all."""
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
        """Test that `get_subject()` returns the correct subject."""
        dummy_subject = 'testsubject'
        expected_value = 'Re: testsubject'
        self.view.object = Mock(subject=dummy_subject)

        actual_value = self.view.get_subject()

        self.assertEqual(actual_value, expected_value)

    def test_get_subject_already_replied(self):
        """Test that `get_subject()` does not alter the subject, when it is already prefixed."""
        expected_value = 'Re: testsubject'
        self.view.object = Mock(subject=expected_value)

        actual_value = self.view.get_subject()

        self.assertEqual(actual_value, expected_value)

    @patch('inyoka.privmsg.views.quote_text')
    def test_get_text(self, mock_quote_text):
        """Test that `get_text()` returns the correct message text."""
        expected_text = 'test text'
        expected_user = User(username='testuser')
        self.view.object = Mock(author=expected_user, text=expected_text)

        self.view.get_text()

        mock_quote_text.assert_called_once_with(
            text=expected_text,
            author=expected_user
        )


class TestMessageReplyViewIntegration(TestCase):
    """Integration Tests for `MessageReplyView`."""

    def setUp(self):
        """Set up testing users and messages."""
        self.author = User.objects.register_user(
            username='author',
            email='author',
            password='author',
            send_mail=False,
        )
        self.recipient = User.objects.register_user(
            username='recipient',
            email='recipient',
            password='recipient',
            send_mail=False,
        )
        self.recipient2 = User.objects.register_user(
            username='recipient2',
            email='recipient2',
            password='recipient2',
            send_mail=False,
        )
        MessageData.send(
            author=self.author,
            recipients=[self.recipient, self.recipient2],
            subject='testsubject',
            text='testmessage',
        )
        self.message = self.author.message_set.sent().first()
        self.received_message = self.recipient.message_set.inboxed().first()

    def test_messagereplyview_with_invalid_message(self):
        """Test that trying to reply to a message not belonging to the user gives a 404."""
        self.client.login(username='recipient', password='recipient')
        url = reverse('privmsg-message-reply', args=(self.message.id,))
        response = self.client.get(url)
        self.assertEqual(404, response.status_code)

    def test_messagereplyview_with_valid_message(self):
        """Test that trying to reply to a message returns a pre-filled form."""
        self.client.login(username='recipient', password='recipient')
        url = reverse('privmsg-message-reply', args=(self.received_message.id,))
        response = self.client.get(url)
        self.assertIn('form', response.context_data)
        self.assertEqual('Re: testsubject', response.context_data['form']['subject'].value())
        self.assertIn('> testmessage', response.context_data['form']['text'].value())

    def test_messagereplyview_reply_to_all(self):
        """Test that replying to all returns a pre-filled form."""
        self.client.login(username='recipient', password='recipient')
        url = reverse('privmsg-message-reply-all', args=(self.received_message.id,))
        response = self.client.get(url)
        self.assertIn('form', response.context_data)
        self.assertEqual('Re: testsubject', response.context_data['form']['subject'].value())
        self.assertIn('> testmessage', response.context_data['form']['text'].value())


class TestMessageReplyReportedTopicView(TestCase):
    """Unit tests for `MessageReplyReportedTopicView`."""

    def setUp(self):
        """Set up the view for testing."""
        self.request = RequestFactory().get('/')
        self.user = Mock()
        self.view = MessageReplyReportedTopicView()
        self.view.request = self.request
        self.view.request.user = self.user

    @patch('inyoka.privmsg.views.Topic.objects.get')
    def test_get_object(self, mock_topic_objects_get):
        """Test that `get_object()` returns the reported topic."""
        expected_object = 'test'
        mock_topic_objects_get.return_value = expected_object
        self.view.kwargs = {'slug': 'test_slug'}

        actual_object = self.view.get_object()

        self.assertEqual(expected_object, actual_object)
        mock_topic_objects_get.assert_called_once_with(slug='test_slug')

    @patch('inyoka.privmsg.views.User')
    def test_get_recipients(self, mock_user):
        """Test that `get_recipients()` returns the correct recipients usernames."""
        expected_value = 'testuser'
        self.view.object = Mock()
        mock_user.objects.get.return_value = User(username=expected_value)

        actual_value = self.view.get_recipients()

        self.assertEqual(actual_value, expected_value)

    def test_get_subject(self):
        """Test that `get_subject()` returns the correct subject."""
        dummy_subject = 'testsubject'
        expected_value = 'Re: testsubject'
        self.view.object = Mock(title=dummy_subject)

        actual_value = self.view.get_subject()

        self.assertEqual(actual_value, expected_value)

    @patch('inyoka.privmsg.views.quote_text')
    def test_get_text(self, mock_quote_text):
        """Test that `get_text()` returns the correct message text."""
        expected_text = 'test text'
        expected_user = User(username='testuser')
        self.view.object = Mock(author=expected_user, reported=expected_text)

        self.view.get_text()

        mock_quote_text.assert_called_once_with(
            text=expected_text,
            author=expected_user
        )


class TestMessageReplyReportedTopicViewIntegration(TestCase):
    """Integration Tests for `MessageReplyReportedTopicView`."""

    def setUp(self):
        """Set up testing users and reported topic."""
        # users
        self.privileged_user = User.objects.register_user(
            username='mod',
            email='mod',
            password='mod',
            send_mail=False,
        )
        self.unprivileged_user = User.objects.register_user(
            username='noob',
            email='noob',
            password='noob',
            send_mail=False,
        )
        self.privileged_user._permissions = PERMISSION_MAPPING['manage_topics']  # TODO: new permissions
        self.privileged_user.save()

        # forum and topic
        self.forum = Forum.objects.create(name='testforum')
        self.topic = Topic.objects.create(
            title='testtopic',
            author=self.unprivileged_user,
            forum=self.forum,
        )

        # report the topic
        self.topic.reported = 'testreport'
        self.topic.reporter_id = self.unprivileged_user.pk
        self.topic.save()

    def test_messagereplyreportedtopicview_as_normal_user(self):
        """Test that trying to reply to a report as unprivileged user gives a 403."""
        url = reverse('privmsg-reply-reported', args=(self.topic.slug,))
        self.client.login(username='noob', password='noob')
        response = self.client.get(url)
        self.assertEqual(403, response.status_code)
        # Note: Since the slug in the URL leaks information, I think the error code should be 404

    def test_messagereplyreportedtopicview_as_privileged_user(self):
        """Test that trying to reply to a report as privileged user contains reported topic data."""
        url = reverse('privmsg-reply-reported', args=(self.topic.slug,))
        self.client.login(username='mod', password='mod')
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEqual('Re: testtopic', response.context_data['form']['subject'].value())
        self.assertEqual(self.unprivileged_user.username, response.context_data['form']['recipients'].value())


class TestMessageReplySuggestedArticleView(TestCase):
    """Unit tests for `MessageReplySuggestedArticleView`."""

    def setUp(self):
        """Set up the view for testing."""
        self.request = RequestFactory().get('/')
        self.user = Mock()
        self.view = MessageReplySuggestedArticleView()
        self.view.request = self.request
        self.view.request.user = self.user

    @patch('inyoka.privmsg.views.Suggestion.objects.get')
    def test_get_object(self, mock_suggestion_objects_get):
        """Test that `get_object()` returns the suggested article."""
        expected_value = 'test_suggestion'
        mock_suggestion_objects_get.return_value = expected_value
        self.view.kwargs = {'pk': 'some_value'}

        actual_value = self.view.get_object()

        self.assertEqual(expected_value, actual_value)
        mock_suggestion_objects_get.called_once_with(pk='some_value')

    def test_get_recipients(self):
        """Test `get_recipients()` returns the correct list of recipients."""
        expected_value = 'testuser'
        self.view.object = Mock(author=User(username=expected_value))

        actual_value = self.view.get_recipients()

        self.assertEqual(actual_value, expected_value)

    def test_get_subject(self):
        """Test that `get_subject()` returns the correct subject string."""
        dummy_subject = 'testsubject'
        expected_value = 'Re: testsubject'
        self.view.object = Mock(title=dummy_subject)

        actual_value = self.view.get_subject()

        self.assertEqual(actual_value, expected_value)

    @patch('inyoka.privmsg.views.quote_text')
    def test_get_text(self, mock_quote_text):
        """Test that `get_text()` returns the correct message text."""
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


class TestMessageReplySuggestedArticleViewIntegration(TestCase):
    """Integration Tests for `MessageReplySuggestedArticleView`."""

    def setUp(self):
        """Set up testing users and a suggestion."""
        self.privileged_user = User.objects.register_user(
            username='author',
            email='author',
            password='author',
            send_mail=False,
        )
        self.unprivileged_user = User.objects.register_user(
            username='noob',
            email='noob',
            password='noob',
            send_mail=False,
        )
        self.privileged_user._permissions = PERMISSION_MAPPING['article_edit']  # TODO: new permissions
        self.privileged_user.save()

        # forum and topic
        self.suggestion = Suggestion.objects.create(
            author=self.unprivileged_user,
            title='testsuggestion',
            intro='testintro',
            text='testtext',
            notes='testnotes',
        )

    def test_messagereplysuggestedarticle_as_privileged_user(self):
        """Test that replying to an article suggestion as a privileged user returns a pre-filled form."""
        self.client.login(username='author', password='author')
        url = reverse_lazy('privmsg-reply-suggestion', args=(self.suggestion.id,))
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEqual('Re: testsuggestion', response.context_data['form']['subject'].value())
        self.assertEqual(self.unprivileged_user.username, response.context_data['form']['recipients'].value())

    def test_messagereplysuggestedarticle_as_unprivileged_user(self):
        """Test that replying to an article suggestion as an unprivileged user returns a 403."""
        self.client.login(username='noob', password='noob')
        url = reverse_lazy('privmsg-reply-suggestion', args=(self.suggestion.id,))
        response = self.client.get(url)
        self.assertEqual(403, response.status_code)


class TestMultiMessageProcessView(TestCase):
    """Unit Tests for `MultiMessageProcessView`."""

    def setUp(self):
        """Set up the view for testing."""
        self.request = RequestFactory().get('/')
        self.user = Mock()
        self.view = MultiMessageProcessView()
        self.view.request = self.request
        self.view.request.user = self.user

    @patch('inyoka.privmsg.views.FormMixin.get_form_kwargs')
    def test_get_form_kwargs(self, mock_get_form_kwargs):
        """Test `get_form_kwargs()` returns a dict containing the queryset."""
        expected_value = 'queryset'
        mock_get_form_kwargs.return_value = {}
        self.view.get_queryset = Mock(return_value=expected_value)

        actual_value = self.view.get_form_kwargs()

        self.assertEqual(actual_value['queryset'], expected_value)

    def test_get_queryset(self):
        """Test the `get_queryset()` method."""
        expected_value = 'Faked'
        self.view.request.user.message_set = expected_value

        actual_value = self.view.get_queryset()

        self.assertEqual(actual_value, expected_value)

    def test_post_when_form_is_valid(self):
        """Test `post()` method calls `form_valid()` when form successfully validates."""
        mock_form = Mock()
        mock_form.is_valid = Mock(return_value=True)
        mock_get_form = Mock(return_value=mock_form)
        self.view.get_form = mock_get_form
        self.view.form_valid = Mock(return_value=True)

        self.view.post(self.request)

        self.view.form_valid.called_once_with(self.view.get_form)

    def test_post_when_form_is_invalid(self):
        """Test `post()` raises a 404 error when form is not valid."""
        mock_form = Mock()
        mock_form.is_valid = Mock(return_value=False)
        mock_get_form = Mock(return_value=mock_form)
        self.view.get_form = mock_get_form

        with self.assertRaises(Http404):
            self.view.post(self.request)

    @patch('inyoka.privmsg.views.HttpResponseRedirect')
    def test_form_valid_with_action_archive(self, mock_redirect):
        """Test `form_valid()` calls `bulk_archive()` when called with action "archive"."""
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
        """Test that `form_valid()` calls `bulk_trash()` when called with action "trash"."""
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
        """Test `form_valid()` calls `bulk_restore()` when called with action "restore"."""
        mocked_queryset = Mock()
        form = MultiMessageSelectForm(queryset=mocked_queryset)
        form.cleaned_data = {
            'selected_messages': mocked_queryset,
            'action': 'restore',
        }

        self.view.form_valid(form)

        mocked_queryset.assert_has_calls([call.bulk_restore()])
        mock_redirect.assert_called_once_with(reverse_lazy('privmsg-inbox'))


class TestMultiMessageProcessViewIntegration(TestCase):
    """Integration Tests for `MultiMessageProcessView`."""

    def setUp(self):
        self.author = User.objects.register_user(
            username='author',
            email='author',
            password='author',
            send_mail=False,
        )
        self.recipient = User.objects.register_user(
            username='recipient',
            email='recipient',
            password='recipient',
            send_mail=False
        )
        MessageData.send(
            author=self.author,
            recipients=[self.recipient],
            subject='message1',
            text='text',
        )
        MessageData.send(
            author=self.author,
            recipients=[self.recipient],
            subject='message2',
            text='text',
        )
        self.received_messages = self.recipient.message_set.inboxed().all()

    def test_multimessageprocessview_with_invalid_ids(self):
        """Test that submitting a form with invalid ids raises a 404 error."""
        self.client.login(username='recipient', password='recipient')
        url = reverse_lazy('privmsg-bulk-process')
        data = {
            'selected_messages': [1, 2],
            'action': 'archive',
        }
        response = self.client.post(url, data)
        self.assertEqual(404, response.status_code)

    def test_multimessageprocessview_with_invalid_action(self):
        """Test that submitting a form with invalid action raises a 404 error."""
        self.client.login(username='recipient', password='recipient')
        url = reverse_lazy('privmsg-bulk-process')
        data = {
            'selected_messages': [2, 4],
            'action': 'WRONG',
        }
        response = self.client.post(url, data)
        self.assertEqual(404, response.status_code)

    def test_multimessageprocessview_with_valid_data(self):
        """Test that submitting the form with valid data redirects to the correct folder."""
        self.client.login(username='recipient', password='recipient')
        url = reverse_lazy('privmsg-bulk-process')
        data = {
            'selected_messages': [m.id for m in self.received_messages],
            'action': 'archive',
        }
        response = self.client.post(url, data)
        self.assertEqual(302, response.status_code)
        self.assertIn(reverse('privmsg-archive'), response.url)
