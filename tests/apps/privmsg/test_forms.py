# -*- coding: utf-8 -*-
"""
    tests.apps.privmsg.test_models
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test privmsg models.

    :copyright: (c) 2011-2015 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from mock import patch

from django.core.exceptions import ValidationError

from inyoka.privmsg.forms import MessageComposeForm, MultiUserField, MultiGroupField, PrivilegedMessageComposeForm
from inyoka.portal.user import deactivate_user, User, Group, PERMISSION_NAMES
from inyoka.utils.test import TestCase


class TestMultiUserField(TestCase):
    def setUp(self):
        """
        Set up three users to test the MultiUserField.
        """
        self.user1 = User.objects.register_user(username='user1', email='user1', password='', send_mail=False)
        self.user2 = User.objects.register_user(username='user2', email='user2', password='', send_mail=False)
        self.user3 = User.objects.register_user(username='user3', email='user3', password='', send_mail=False)

    def test_multiuserfield_with_one_user(self):
        """
        Test that the MultiUserField returns a list of one user object, when one user is given.
        """
        field = MultiUserField(separator=';')
        data = field.clean(self.user1.username)
        self.assertEqual(data, [self.user1])

    def test_multiuserfield_with_user_list(self):
        """
        Test that MultiUserField returns a list of user objects when multiple usernames are given.
        """
        field = MultiUserField(separator=';')
        data = field.clean('user1; user2;user3')
        self.assertListEqual(data, [self.user1, self.user2, self.user3])

    def test_multiuserfield_with_nonexistant_user(self):
        """
        Test that MultiUserField raises a ValidationError when a nonexistant user is given.
        """
        field = MultiUserField(separator=';')
        with self.assertRaises(ValidationError) as cm:
            field.clean('user1; user4; user3')
        self.assertEqual(cm.exception.code, 'recipient_does_not_exist')


class TestMultiGroupField(TestCase):
    def setUp(self):
        """
        Set up three users to test the MultiUserField.
        """
        self.user1 = User.objects.register_user(username='user1', email='user1', password='', send_mail=False)
        self.user2 = User.objects.register_user(username='user2', email='user2', password='', send_mail=False)
        self.user3 = User.objects.register_user(username='user3', email='user3', password='', send_mail=False)
        self.group1 = Group.objects.create(name='group1')
        self.group1.user_set.add(self.user1)
        self.group1.user_set.add(self.user2)
        self.group2 = Group.objects.create(name='group2')
        self.group2.user_set.add(self.user1)
        self.group2.user_set.add(self.user3)

    def test_multigroupfield_with_one_group(self):
        """
        Test that the MultiGroupField returns a list of user objects that belong to a given group.
        """
        field = MultiGroupField(separator=';')
        data = field.clean(self.group1.name)
        self.assertListEqual(data, list(self.group1.user_set.all()))

    def test_multigroupfield_with_group_list(self):
        """
        Test that the MultiGroupField returns a list of user objects that belong to multiple given groups.
        """
        field = MultiGroupField(separator=';')
        data = field.clean('group1; group2')
        self.assertListEqual(data, [self.user1, self.user2, self.user3])

    def test_multigroupfield_with_nonexistant_group(self):
        """
        Test that the MultiGroupField returns a ValidationError, when a given group does not exist.
        """
        field = MultiGroupField(separator=';')
        with self.assertRaises(ValidationError) as cm:
            field.clean('group1; group3')
        self.assertEqual(cm.exception.code, 'group_recipient_does_not_exist')


class TestComposeForm(TestCase):
    def setUp(self):
        """
        Make sure we have some test users and groups we can message during our tests.
        """
        # define users and groups
        user_definitions = (('privileged_user', 'privileged'),
                            ('normal_user', 'normal'),
                            ('inactive_user', 'inactive'),
                            ('group_1_user_1', 'unprivileged1'),
                            ('group_1_user_2', 'unprivileged2'),
                            ('group_2_user_1', 'unprivileged3'),
                            ('group_2_user_2', 'unprivileged4'),)
        group_definitions = ('group_1', 'group_2')
        permissions = sum(PERMISSION_NAMES.keys())

        self.users = {}
        self.groups = {}

        # create users
        for name, email in user_definitions:
            self.users[name] = User.objects.register_user(username=name, email=email, password='', send_mail=False)

        # create groups
        for groupname in group_definitions:
            self.groups[groupname] = Group.objects.create(name=groupname)

        # adjust some users.
        self.users['privileged_user']._permissions = permissions
        self.users['privileged_user'].save()
        deactivate_user(self.users['inactive_user'])

        # add users to groups
        self.groups['group_1'].user_set.add(self.users['group_1_user_1'])
        self.groups['group_1'].user_set.add(self.users['group_1_user_2'])
        self.groups['group_1'].user_set.add(self.users['privileged_user'])

        self.groups['group_2'].user_set.add(self.users['group_2_user_1'])
        self.groups['group_2'].user_set.add(self.users['group_2_user_2'])
        self.groups['group_2'].user_set.add(self.users['privileged_user'])

    def test_composeform_init(self):
        """
        Test the constructor of `ComposeForm`.
        """
        MessageComposeForm(user=self.users['normal_user'])

    def test_composeform_init_without_user(self):
        """
        Test that `ComposeForm` requires `user` argument.
        """
        with self.assertRaises(KeyError):
            MessageComposeForm()

    @patch('inyoka.utils.sessions.SurgeProtectionMixin.clean')
    def test_composeform_valid_data(self, mock_spm_clean):
        """
        Test `ComposeForm` with valid input.
        """
        form = MessageComposeForm(user=self.users['normal_user'],
                           data={'recipients': u'privileged_user',
                                 'subject': u'Test',
                                 'text': u'Test'})
        self.assertTrue(form.is_valid())

    def test_composeform_recipient_does_not_exist(self):
        """
        Test ComposeForm with recipient who does not exist.
        """
        form = MessageComposeForm(user=self.users['normal_user'],
                           data={'recipients': u'not_present',
                                 'subject': u'Test',
                                 'text': u'Test'})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors.as_data()['recipients'][0].code,
                         'recipient_does_not_exist')

        form = MessageComposeForm(user=self.users['normal_user'],
                           data={'recipients': u'privileged_user; not_present',
                                 'subject': u'Test',
                                 'text': u'Test'})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors.as_data()['recipients'][0].code,
                         'recipient_does_not_exist')

    def test_composeform_recipient_is_inactive(self):
        """
        Test ComposeForm with inactive recipients.
        """
        form = MessageComposeForm(user=self.users['normal_user'],
                           data={'recipients': u'inactive_user',
                                 'subject': u'Test',
                                 'text': u'Test'})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors.as_data()['recipients'][0].code,
                         'recipient_is_inactive')

        form = MessageComposeForm(user=self.users['normal_user'],
                           data={'recipients': u'privileged_user; inactive_user',
                                 'subject': u'Test',
                                 'text': u'Test'})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors.as_data()['recipients'][0].code,
                         'recipient_is_inactive')

    def test_composeform_recipient_is_self(self):
        """
        Test `ComposeForm` whith users attempting to send messages to themselves.
        """
        form = MessageComposeForm(user=self.users['normal_user'],
                           data={'recipients': u'normal_user',
                                 'subject': u'Test',
                                 'text': u'Test'})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors.as_data()['recipients'][0].code,
                         'recipient_is_self')

    def test_composeform_recipient_is_system_user(self):
        """
        Test `ComposeForm` when `recipients` contains a system user.
        """
        form = MessageComposeForm(user=self.users['normal_user'],
                           data={'recipients': User.objects.get_system_user().username,
                                 'subject': u'Test',
                                 'text': u'Test'})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors.as_data()['recipients'][0].code,
                         'recipient_is_system_user')

    def test_composeform_missing_subject(self):
        """
        Test `ComposeForm` without a subject.
        """
        form = MessageComposeForm(user=self.users['normal_user'],
                           data={'recipients': self.users['privileged_user'].username,
                                 'text': u'Test'})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors.as_data()['subject'][0].code,
                         'required')

    def test_composeform_missing_text(self):
        """
        Test `ComposeForm` without a text.
        """
        form = MessageComposeForm(user=self.users['normal_user'],
                           data={'recipients': self.users['privileged_user'].username,
                                 'subject': u'Test'})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors.as_data()['text'][0].code,
                         'required')

    def test_composeform_group_recipient_does_not_exist(self):
        """
        Test `ComposeForm` when a nonexistant group is given as `group_recipient`.
        """
        form = PrivilegedMessageComposeForm(user=self.users['privileged_user'],
                                            data={'recipients': self.users['normal_user'].username,
                                                  'group_recipients': 'non_existant',
                                                  'subject': u'Test',
                                                  'text': u'Test'})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors.as_data()['group_recipients'][0].code,
                         'group_recipient_does_not_exist')

        form = PrivilegedMessageComposeForm(user=self.users['privileged_user'],
                                            data={'recipients': self.users['normal_user'].username,
                                                  'group_recipients': 'group_1; non_existant',
                                                  'subject': u'Test',
                                                  'text': u'Test'})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors.as_data()['group_recipients'][0].code,
                         'group_recipient_does_not_exist')

    @patch('inyoka.utils.sessions.SurgeProtectionMixin.clean')
    def test_composeform_only_group_recipients(self, mock_spm_clean):
        """
        Test `ComposeForm` when a group_recipient is given but no regular recipient.
        """
        form = PrivilegedMessageComposeForm(user=self.users['privileged_user'],
                                            data={'group_recipients': 'group_1',
                                                  'subject': u'Test',
                                                  'text': u'Test'})
        self.assertTrue(form.is_valid())
        # Note that privileged_user is a member of group_1 but can not message himself
        # so is exluded from the list of recipients.
        self.assertListEqual(form.cleaned_data['recipients'],
                            [self.users['group_1_user_1'], self.users['group_1_user_2']])

    @patch('inyoka.utils.sessions.SurgeProtectionMixin.clean')
    def test_composeform_multiple_group_recipients(self, mock_spm_clean):
        """
        Test `ComposeForm` with multiple groups.
        """
        form = PrivilegedMessageComposeForm(user=self.users['privileged_user'],
                                            data={'recipients': u'normal_user',
                                                  'group_recipients': u'group_1; group_2',
                                                  'subject': u'Test',
                                                  'text': u'Test'})
        expected_recipients = set()
        expected_recipients.update(self.groups['group_1'].user_set.all())
        expected_recipients.update(self.groups['group_2'].user_set.all())
        expected_recipients.update([self.users['normal_user']])
        expected_recipients.discard(self.users['privileged_user'])
        self.assertTrue(form.is_valid())
        self.assertListEqual(form.cleaned_data['recipients'],
                             list(expected_recipients))
