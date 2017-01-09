# -*- coding: utf-8 -*-
"""
    tests.apps.privmsg.test_forms
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test privmsg forms.

    :copyright: (c) 2011-2015 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.core.exceptions import ValidationError
from inyoka.portal.user import PERMISSION_NAMES, Group, User
from inyoka.privmsg.forms import (
    CSVField,
    MessageComposeForm,
    MultiGroupField,
    MultiMessageSelectForm,
    MultiUserField,
    PrivilegedMessageComposeForm,
)
from inyoka.utils.test import TestCase
from mock import patch, Mock


class TestCSVField(TestCase):
    """CSVField Unit Tests."""

    def test_csvfield_single_word(self):
        """Test CSVField with a single word input."""
        field = CSVField()
        input_string = 'test'
        expected_value = ['test']

        actual_value = field.to_python(input_string)

        self.assertListEqual(actual_value, expected_value)

    def test_csvfield_single_word_trailing_separator(self):
        """Test CSVField should ignore trailing separators."""
        field = CSVField()
        input_string = 'test,'
        expected_value = ['test']

        actual_value = field.to_python(input_string)

        self.assertListEqual(actual_value, expected_value)

    def test_csvfield_multiple_words(self):
        """Test CSVField should split multiple items at separator character."""
        field = CSVField()
        input_string = 'test,test2'
        expected_value = ['test', 'test2']

        actual_value = field.to_python(input_string)

        self.assertListEqual(actual_value, expected_value)

    def test_csvfield_multiple_words_strip_spaces(self):
        """Test CSVField should ignore spaces around separators."""
        field = CSVField()
        input_string = 'test, test2'
        expected_value = ['test', 'test2']

        actual_value = field.to_python(input_string)

        self.assertListEqual(actual_value, expected_value)

    def test_csvfield_multiple_multiple_words_semicolon(self):
        """Test CSVField with different separator character."""

        field = CSVField(separator=';')
        input_string = 'test; test2'
        expected_value = ['test', 'test2']

        actual_value = field.to_python(input_string)

        self.assertListEqual(actual_value, expected_value)

    def test_csvfield_multiple_words_deduplicate(self):
        """Test CSVField configured to ignore duplicate items in the return list."""
        field = CSVField(deduplicate=True)
        input_string = 'test, test, test2'
        expected_value = ['test', 'test2']

        actual_value = field.to_python(input_string)

        self.assertListEqual(actual_value, expected_value)

    def test_csvfield_multiple_words_deduplicate_semicolon(self):
        """Test CSVField with custom separator and ignoring duplicates."""
        field = CSVField(separator=';', deduplicate=True)
        input_string = 'test; test; test2'
        expected_value = ['test', 'test2']

        actual_value = field.to_python(input_string)

        self.assertListEqual(actual_value, expected_value)

    def test_csvfield_multiple_words_wrong_separator(self):
        """Test CSVField should ignore wrong separator characters."""
        field = CSVField()
        input_string = 'test;test2'
        expected_value = ['test;test2']

        actual_value = field.to_python(input_string)

        self.assertListEqual(actual_value, expected_value)


class TestMultiUserField(TestCase):
    """MultiUserField Unit Tests."""

    @classmethod
    def setUpTestData(cls):
        """Set up three users to test the MultiUserField."""
        cls.user1 = User(username='user1')
        cls.user2 = User(username='user2')
        cls.user3 = User(username='user3')
        cls.field = MultiUserField(separator=';', deduplicate=True)

    @patch('inyoka.portal.user.User.objects.filter')
    def test_multiuserfield_with_one_user(self, mock_user_filter):
        """Test that MultiUserField should return a list of one user object, when one user is given."""
        input_string = self.user1.username
        expected_users = [self.user1]
        mock_user_filter.return_value = expected_users

        actual_users = self.field.clean(input_string)

        self.assertListEqual(actual_users, expected_users)

    @patch('inyoka.portal.user.User.objects.filter')
    def test_multiuserfield_with_duplicate_user(self, mock_user_filter):
        """Test that the MultiUserField ignores duplicate users."""
        input_string = 'user1; user1'
        expected_users = [self.user1]
        mock_user_filter.return_value = expected_users

        actual_users = self.field.clean(input_string)

        self.assertListEqual(actual_users, expected_users)

    @patch('inyoka.portal.user.User.objects.filter')
    def test_multiuserfield_with_user_list(self, mock_user_filter):
        """Test that MultiUserField returns a list of user objects when multiple usernames are given."""
        input_string = 'user1; user2;user3'
        expected_users = [self.user1, self.user2, self.user3]
        mock_user_filter.return_value = expected_users

        actual_users = self.field.clean(input_string)

        self.assertListEqual(actual_users, expected_users)

    @patch('inyoka.portal.user.User.objects.filter')
    def test_multiuserfield_with_nonexistant_user(self, mock_user_filter):
        """Test that MultiUserField raises a ValidationError when a nonexistant user is given."""
        input_string = 'user1; missing; user3'
        expected_users = [self.user1, self.user3]
        mock_user_filter.return_value = expected_users

        with self.assertRaises(ValidationError) as cm:
            self.field.clean(input_string)

        self.assertEqual(cm.exception.code, 'recipient_does_not_exist')


class TestMultiGroupField(TestCase):
    """MultiGroupField Unit Tests."""

    @classmethod
    def setUpTestData(cls):
        """Set up three users to test the MultiUserField."""
        cls.user1 = User(username='user1')
        cls.user2 = User(username='user2')
        cls.user3 = User(username='user3')
        cls.group1 = Group(name='group1')
        cls.group2 = Group(name='group2')
        cls.field = MultiGroupField(separator=';', deduplicate=True)

    @patch('inyoka.portal.user.Group.objects.filter')
    @patch('inyoka.portal.user.User.objects.filter')
    def test_multigroupfield_with_one_group(self, mock_user_filter, mock_group_filter):
        """Test that the MultiGroupField returns a list of user objects that belong to a given group."""
        input_string = 'group1'
        expected_users = [self.user1, self.user2]
        mock_group_filter.return_value = [self.group1]
        mock_user_filter.return_value.distinct.return_value = expected_users

        actual_users = self.field.clean(input_string)

        self.assertListEqual(actual_users, expected_users)

    @patch('inyoka.portal.user.Group.objects.filter')
    @patch('inyoka.portal.user.User.objects.filter')
    def test_multigroupfield_with_group_list(self, mock_user_filter, mock_group_filter):
        """Test that the MultiGroupField returns a list of user objects that belong to given groups."""
        input_string = 'group1; group2'
        expected_users = [self.user1, self.user2, self.user3]
        mock_group_filter.return_value = [self.group1, self.group2]
        mock_user_filter.return_value.distinct.return_value = expected_users

        actual_users = self.field.clean(input_string)

        self.assertListEqual(actual_users, expected_users)

    @patch('inyoka.portal.user.Group.objects.filter')
    def test_multigroupfield_with_nonexistant_group(self, mock_group_filter):
        """Test that the MultiGroupField returns a ValidationError, when a given group does not exist."""
        input_string = 'group1; missing_group'
        mock_group_filter.return_value = [self.group1]

        with self.assertRaises(ValidationError) as cm:
            self.field.clean(input_string)

        self.assertEqual(cm.exception.code, 'group_recipient_does_not_exist')


class TestComposeForm(TestCase):
    """MessageComposeForm and PrivilegedMessageComposeForm Tests."""

    @classmethod
    def setUpTestData(cls):
        cls.system_user = User.objects.get_system_user()  # hits the database!
        cls.normal_user = User(pk=10, username='normal', status=1)
        cls.inactive_user = User(pk=11, username='inactive', status=0)
        cls.privileged_user = User(pk=12, username='privileged', status=1)
        cls.privileged_user._permissions = sum(PERMISSION_NAMES.keys())  # TODO: new permissions

    def test_composeform_init(self):
        """Test the init of `MessageComposeForm`."""
        MessageComposeForm(user=self.normal_user)

    def test_composeform_init_without_user(self):
        """Test that `MessageComposeForm` requires `user` argument."""
        with self.assertRaises(KeyError):
            MessageComposeForm()

    def test_composeform_clean_recipients_single_valid_recipient(self):
        """Test recipient field validation, should pass when recipient is valid."""
        expected_recipients = [self.normal_user]
        form = MessageComposeForm(user=self.privileged_user)
        form.cleaned_data = {'recipients': expected_recipients}

        actual_recipients = form.clean_recipients()

        self.assertListEqual(actual_recipients, expected_recipients)

    def test_composeform_clean_recipients_multiple_valid_recipient(self):
        """Test recipient field validation, should pass when recipients are valid."""
        expected_recipients = [self.normal_user, self.privileged_user]
        form = MessageComposeForm(user=self.system_user)
        form.cleaned_data = {'recipients': expected_recipients}

        actual_recipients = form.clean_recipients()

        self.assertListEqual(actual_recipients, expected_recipients)

    def test_composeform_clean_recipients_self(self):
        """Test recipient field validation, should raise error when recipient is self."""
        expected_recipients = [self.privileged_user]
        form = MessageComposeForm(user=self.privileged_user)
        form.cleaned_data = {'recipients': expected_recipients}

        with self.assertRaises(ValidationError) as cm:
            form.clean_recipients()

        self.assertEqual(cm.exception.code, 'recipient_is_self')

    def test_composeform_clean_recipients_system_user_recipient(self):
        """Test recipient field validation, should raise error when recipient is system user."""
        expected_recipients = [self.system_user]
        form = MessageComposeForm(user=self.privileged_user)
        form.cleaned_data = {'recipients': expected_recipients}

        with self.assertRaises(ValidationError) as cm:
            form.clean_recipients()

        self.assertEqual(cm.exception.code, 'recipient_is_system_user')

    def test_composeform_clean_recipients_inactive_recipient(self):
        """Test recipient field validation, should raise error when recipient is inactive."""
        expected_recipients = [self.inactive_user]
        form = MessageComposeForm(user=self.privileged_user)
        form.cleaned_data = {'recipients': expected_recipients}

        with self.assertRaises(ValidationError) as cm:
            form.clean_recipients()

        self.assertEqual(cm.exception.code, 'recipient_is_inactive')

    def test_composeform_clean_recipients_multiple_including_self(self):
        """Test recipient field validation, should raise error when one recipient is self."""
        expected_recipients = [self.normal_user, self.privileged_user]
        form = MessageComposeForm(user=self.privileged_user)
        form.cleaned_data = {'recipients': expected_recipients}

        with self.assertRaises(ValidationError) as cm:
            form.clean_recipients()

        self.assertEqual(cm.exception.code, 'recipient_is_self')

    def test_composeform_clean_group_recipients(self):
        """Test group recipient field validation, should pass list through."""

        expected_recipients = [self.normal_user]
        form = PrivilegedMessageComposeForm(user=self.privileged_user)
        form.cleaned_data = {'group_recipients': expected_recipients}

        actual_recipients = form.clean_group_recipients()

        self.assertListEqual(actual_recipients, expected_recipients)

    def test_composeform_clean_group_recipients_removes_request_user(self):
        """Test group recipient field validation, should remove active user from list of recipients."""
        given_recipients = [self.normal_user, self.privileged_user]
        expected_recipients = [self.normal_user]
        form = PrivilegedMessageComposeForm(user=self.privileged_user)
        form.cleaned_data = {'group_recipients': given_recipients}

        actual_recipients = form.clean_group_recipients()

        self.assertListEqual(actual_recipients, expected_recipients)

    def test_composeform_clean_joins_recipients_and_group_recipients(self):
        """Test that `clean()` joins lists of recipients and group_recipients."""
        given_recipients = [self.normal_user]
        given_group_recipients = [self.system_user]
        expected_recipients = [self.normal_user, self.system_user]
        form = PrivilegedMessageComposeForm(user=self.privileged_user)
        form.cleaned_data = {
            'recipients': given_recipients,
            'group_recipients': given_group_recipients,
        }

        actual_recipients = form.clean()

        self.assertItemsEqual(actual_recipients['recipients'], expected_recipients)

    def test_composeform_clean_with_recipients(self):
        """Test that `clean()` works as expected with only recipients."""
        given_recipients = [self.normal_user, self.privileged_user]
        expected_recipients = given_recipients
        form = PrivilegedMessageComposeForm(user=self.privileged_user)
        form.cleaned_data = {
            'recipients': given_recipients,
            'group_recipients': [],
        }

        actual_recipients = form.clean()

        self.assertItemsEqual(actual_recipients['recipients'], expected_recipients)

    def test_composeform_clean_with_group_recipients(self):
        """Test that `clean()` works with only group recipients."""
        given_group_recipients = [self.normal_user, self.privileged_user]
        expected_recipients = given_group_recipients
        form = PrivilegedMessageComposeForm(user=self.privileged_user)
        form.cleaned_data = {
            'recipients': [],
            'group_recipients': given_group_recipients,
        }

        actual_recipients = form.clean()

        self.assertItemsEqual(actual_recipients['recipients'], expected_recipients)

    def test_composeform_clean_without_any_recipients(self):
        """Test that `clean()` throws an error when no recipients are given."""
        form = PrivilegedMessageComposeForm(user=self.privileged_user)
        form.cleaned_data = {
            'recipients': [],
            'group_recipients': []
        }

        with self.assertRaises(ValidationError) as cm:
            form.clean()

        self.assertEqual(cm.exception.code, 'required')


class TestComposeFormIntegration(TestCase):
    """Integration tests for ComposeForm."""

    @classmethod
    def setUpTestData(cls):
        """Make sure we have some test users and groups we can message during our tests."""
        cls.first_user = User.objects.register_user(
            username='first',
            email='first',
            password='',
            send_mail=False,
        )
        cls.second_user = User.objects.register_user(
            username='second',
            email='second',
            password='',
            send_mail=False,
        )
        cls.group = Group.objects.create(name='group')
        cls.group.user_set = [cls.first_user, cls.second_user]

    def test_composeform_valid_data(self):
        """Test `ComposeForm` with valid input."""
        initial_data = {
            'recipients': self.second_user.username,
            'subject': u'Test',
            'text': u'Test',
        }
        form = MessageComposeForm(
            user=self.first_user,
            data=initial_data,
        )
        form.surge_protection_timeout = None  # deactivate surge protection during tests.

        result = form.is_valid()

        self.assertTrue(result)

    def test_composeform_missing_recipients(self):
        """Test `ComposeForm` without recipients is not valid."""
        initial_data = {
            'subject': u'Test',
            'text': u'Test',
        }
        form = MessageComposeForm(
            user=self.first_user,
            data=initial_data,
        )
        form.surge_protection_timeout = None

        result = form.is_valid()

        self.assertFalse(result)

    def test_composeform_missing_subject(self):
        """Test `ComposeForm` without a subject."""
        initial_data = {
            'recipients': self.second_user.username,
            'text': u'Test',
        }
        form = MessageComposeForm(
            user=self.first_user,
            data=initial_data,
        )
        form.surge_protection_timeout = None

        result = form.is_valid()

        self.assertFalse(result)
        self.assertEqual(form.errors.as_data()['subject'][0].code, 'required')

    def test_composeform_missing_text(self):
        """Test `ComposeForm` without a text."""
        initial_data = {
            'recipients': self.second_user.username,
            'subject': u'Test',
        }
        form = MessageComposeForm(
            user=self.first_user,
            data=initial_data,
        )
        form.surge_protection_timeout = None

        result = form.is_valid()

        self.assertFalse(result)
        self.assertEqual(form.errors.as_data()['text'][0].code, 'required')

    def test_composeform_with_group_recipient(self):
        """Test `PrivilegedMessageComposeForm` with a group recipient is valid."""
        initial_data = {
            'group_recipients': self.group.name,
            'subject': u'Test',
            'text': u'Test',
        }
        form = PrivilegedMessageComposeForm(
            user=self.first_user,
            data=initial_data,
        )

        result = form.is_valid()

        self.assertTrue(result)

    def test_privilegedcomposeform_without_recipient(self):
        """Test `PrivilegedMessageComposeForm` without recipient is not valid."""
        initial_data = {
            'subject': u'Test',
            'text': u'Test',
        }
        form = PrivilegedMessageComposeForm(
            user=self.first_user,
            data=initial_data,
        )

        result = form.is_valid()

        self.assertFalse(result)


class TestMultiMessageSelectForm(TestCase):
    """Tests for the MultiMessageSelectForm."""

    def test_multimessageselectform_init(self):
        """Test form init method."""
        mock_queryset = Mock()
        mock_queryset.values_list.return_value = ((1, ''))

        form = MultiMessageSelectForm(queryset=mock_queryset)

        self.assertEqual(form.queryset, mock_queryset)
        self.assertEqual(mock_queryset.values_list.call_count, 1)
        mock_queryset.values_list.assert_called_once_with('id', 'id')

    def test_multimessageselectform_init_without_queryset(self):
        """Test form initialisation fails without queryset parameter."""
        with self.assertRaises(KeyError):
            MultiMessageSelectForm()

    def test_multimessageselectform_clean_selected_messages(self):
        """Test field validation applies correct filter to queryset and returns the correct queryset."""
        queryset = Mock()
        test_list = [1, 3, 5]
        form = MultiMessageSelectForm(queryset=queryset)
        form.cleaned_data = {'selected_messages': test_list}

        form.clean_selected_messages()

        queryset.filter.assert_called_once_with(pk__in=test_list)


class TestMultiMessageSelectFormIntegration(TestCase):
    def test_multimessageselectform_wrong_action(self):
        """Test form validation fails when an invalid choice for `action` is made."""
        mock_queryset = Mock()
        mock_queryset.values_list.return_value = ((1, 1), (2, 2), (3, 3))
        initial_data = {
            'action': 'nonexistant',
            'selected_messages': [1],
        }
        form = MultiMessageSelectForm(
            queryset=mock_queryset,
            data=initial_data,
        )

        self.assertFalse(form.is_valid())

    def test_multimessageselectform_invalid_message_id(self):
        """Test form validation fails when a message id is passed that does not belong to the user."""
        mock_queryset = Mock()
        mock_queryset.values_list.return_value = ((1, 1), (2, 2), (3, 3))
        initial_data = {
            'action': 'archive',
            'selected_messages': [2, 8],
        }
        form = MultiMessageSelectForm(
            queryset=mock_queryset,
            data=initial_data,
        )

        self.assertFalse(form.is_valid())

    def test_multimessageselectform_valid_data(self):
        """Test form validates successfully with valid inputs."""
        mock_queryset = Mock()
        mock_queryset.values_list.return_value = ((1, 1), (2, 2), (3, 3))
        initial_data = {
            'action': 'archive',
            'selected_messages': [2, 3],
        }
        form = MultiMessageSelectForm(
            queryset=mock_queryset,
            data=initial_data,
        )

        self.assertTrue(form.is_valid())
