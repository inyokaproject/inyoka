# -*- coding: utf-8 -*-
"""
    inyoka.privmsg.forms
    ~~~~~~~~~~~~~~~~~~~~

    Various forms for the private message system

    :copyright: (c) 2007-2016 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from collections import OrderedDict

from django import forms
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy
from inyoka.portal.user import Group, User
from inyoka.utils.sessions import SurgeProtectionMixin


# TODO: Relocate to inyoka.utils.forms?
class CSVField(forms.CharField):
    """
    A Comma Separated Value field. (Why doesn't django have one already?)
    """
    def __init__(self, *args, **kwargs):
        self.separator = kwargs.pop('separator', ',')
        super(CSVField, self).__init__(*args, **kwargs)

    def to_python(self, values):
        if not values:
            return None
        return [v.strip() for v in values.split(self.separator) if v.strip() != u'']


class MultiUserField(CSVField):
    """
    A field that takes multiple usernames and returns a list of user objects.
    """
    def clean(self, values):
        """
        Validate users exist and return a list of user objects.
        """
        values = super(MultiUserField, self).clean(values)

        users = []

        if values is None:
            return users

        for username in values:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                raise forms.ValidationError(_(u'The user “%(username)s” does not exist'),
                                            code='recipient_does_not_exist',
                                            params={'username': username})
            if user not in users:
                users.append(user)

        return users


class MultiGroupField(CSVField):
    """
    A field that takes multiple group names and returns the list of user objects in those groups.
    """
    def clean(self, values):
        """
        Validate that all groups exist and return a list of users in those groups.
        """
        values = super(MultiGroupField, self).clean(values)
        group_users = []
        if values is None:
            return group_users
        for groupname in values:
            try:
                group = Group.objects.get(name=groupname)
            except Group.DoesNotExist:
                raise forms.ValidationError(_(u'The group “%(groupname)s” does not exist.'),
                                            code='group_recipient_does_not_exist',
                                            params={'groupname': groupname})
            group_users += group.user_set.all()
        return list(set(group_users))


class MessageComposeForm(SurgeProtectionMixin, forms.Form):
    """
    Form to compose private messages.
    """
    recipients = MultiUserField(label=ugettext_lazy(u'To'),
                                required=True,
                                separator=';',
                                help_text=ugettext_lazy(u'Separate multiple names by semicolon'))
    subject = forms.CharField(label=ugettext_lazy(u'Subject'),
                              required=True,
                              help_text=ugettext_lazy(u'Please give your message a subject.'))
    text = forms.CharField(label=_(u'Message'),
                           required=True,
                           widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(MessageComposeForm, self).__init__(*args, **kwargs)

    def clean_recipients(self):
        """
        Test if the user has included himself as recipient.
        """
        recipients = self.cleaned_data['recipients']

        reserved_users = (User.objects.get_system_user(),
                          User.objects.get_anonymous_user())

        if self.user in recipients:
            raise forms.ValidationError(_(u'You can not send messages to yourself'),
                                        code='recipient_is_self')
        for user in recipients:
            if user in reserved_users:
                raise forms.ValidationError(_(u'You can not send messages to system users.'),
                                            code='recipient_is_system_user')
            if not user.is_active:
                raise forms.ValidationError(_(u'You can not send messages to inactive users.'),
                                            code='recipient_is_inactive')

        return recipients

    # TODO: Spam protection
    # def clean_text(self):
    #     """
    #     Spam protection
    #     """
    #     return self.cleaned_data['text']


class PrivilegedMessageComposeForm(MessageComposeForm):
    """
    MessageComposeForm for privileged users who can send group messages.
    """
    group_recipients = MultiGroupField(label=ugettext_lazy(u'Groups'),
                                       required=False,
                                       separator=';',
                                       help_text=ugettext_lazy(u'Separate multiple groups by semicolon'))

    class Meta:
        fields = ['recipients', 'group_recipients', 'subject', 'text']

    def __init__(self, *args, **kwargs):
        """
        In this case the recipients field is not required.
        """
        super(PrivilegedMessageComposeForm, self).__init__(*args, **kwargs)
        self.surge_protection_timeout = None
        self.fields['recipients'].required = False

        # reorder the fields
        field_order = ['recipients', 'group_recipients', 'subject', 'text']
        fields = self.fields
        self.fields = OrderedDict((key, fields[key]) for key in field_order)
        # TODO: In django 1.9 this will be as easy as:
        # self.field_order = ['recipients', 'groups_recipients', 'subject', 'text']

    def clean(self):
        """
        Join `recipients` and `group_recipients` so we don't have to do it in the view.
        """
        super(PrivilegedMessageComposeForm, self).clean()
        cleaned_data = self.cleaned_data

        # Join recipients and group recipients lists
        recipients = set()
        recipients.update(cleaned_data.get('recipients', []))
        recipients.update(cleaned_data.get('group_recipients', []))
        cleaned_data['recipients'] = list(recipients)

        # If there are now no recipients, show an error message.
        if len(cleaned_data.get('recipients', [])) == 0:
            raise forms.ValidationError(_(u'Please add a recipient.'),
                                        code='required')

        return cleaned_data

    def clean_group_recipients(self):
        """
        Make sure the user is not in `group_recipients`, if the user can send group messages.
        """
        group_recipients = self.cleaned_data['group_recipients']
        if self.user in group_recipients:
            group_recipients.remove(self.user)
        return group_recipients
