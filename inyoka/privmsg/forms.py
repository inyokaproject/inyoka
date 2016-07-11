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
    """A Comma Separated Value field. (Why doesn't django have one already?)"""

    def __init__(self, *args, **kwargs):
        self.separator = kwargs.pop('separator', ',')
        self.deduplicate = kwargs.pop('deduplicate', False)
        super(CSVField, self).__init__(*args, **kwargs)

    def to_python(self, values):
        if not values:
            return None

        values = [v.strip() for v in values.split(self.separator) if v.strip() != u'']

        if self.deduplicate:
            values = list(set(values))

        return values


class MultiUserField(CSVField):
    """A field that takes multiple usernames and returns a list of user objects."""

    def clean(self, values):
        """Validate users exist and return a list of user objects."""
        values = super(MultiUserField, self).clean(values)

        if values is None:
            return []

        users = User.objects.filter(username__in=values)

        if len(users) != len(values):
            missing_users = set(values) - set(u.username for u in users)
            missing_user = next(iter(missing_users))
            raise forms.ValidationError(
                message=_(u'The user “%(username)s” does not exist'),
                code='recipient_does_not_exist',
                params={'username': missing_user},
            )

        return list(users)


class MultiGroupField(CSVField):
    """A field that takes multiple group names and returns a list of users in those groups."""

    def clean(self, values):
        """Validate that all groups exist and return a list of users in those groups."""
        values = super(MultiGroupField, self).clean(values)

        if values is None:
            return []

        groups = Group.objects.filter(name__in=values)

        if len(groups) != len(values):
            missing_groups = set(values) - set(g.name for g in groups)
            missing_group = next(iter(missing_groups))
            raise forms.ValidationError(
                message=_(u'The group “%(groupname)s” does not exist.'),
                code='group_recipient_does_not_exist',
                params={'groupname': missing_group},
            )

        group_users = User.objects.filter(groups__name__in=values, status=1).distinct()
        return list(group_users)


class MessageComposeForm(SurgeProtectionMixin, forms.Form):
    """Form to compose private messages."""

    recipients = MultiUserField(
        label=ugettext_lazy(u'To'),
        required=True,
        separator=';',
        deduplicate=True,
        help_text=ugettext_lazy(u'Separate multiple names by semicolon'),
    )
    subject = forms.CharField(
        label=ugettext_lazy(u'Subject'),
        required=True,
        help_text=ugettext_lazy(u'Please give your message a subject.'),
    )
    text = forms.CharField(
        label=_(u'Message'),
        required=True,
        widget=forms.Textarea,
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(MessageComposeForm, self).__init__(*args, **kwargs)

    def clean_recipients(self):
        """Test if the user has included himself as recipient."""
        recipients = self.cleaned_data['recipients']

        reserved_users = (User.objects.get_system_user(),
                          User.objects.get_anonymous_user())

        if self.user in recipients:
            raise forms.ValidationError(
                message=_(u'You can not send messages to yourself'),
                code='recipient_is_self',
            )
        for user in recipients:
            if user in reserved_users:
                raise forms.ValidationError(
                    message=_(u'You can not send messages to system users.'),
                    code='recipient_is_system_user',
                )
            if not user.is_active:
                raise forms.ValidationError(
                    message=_(u'You can not send messages to inactive users.'),
                    code='recipient_is_inactive',
                )

        return recipients

    # TODO: Spam protection
    # def clean_text(self):
    #     """
    #     Spam protection
    #     """
    #     return self.cleaned_data['text']


class PrivilegedMessageComposeForm(MessageComposeForm):
    """MessageComposeForm for privileged users who can send group messages."""

    group_recipients = MultiGroupField(
        label=ugettext_lazy(u'Groups'),
        required=False,
        separator=';',
        deduplicate=True,
        help_text=ugettext_lazy(u'Separate multiple groups by semicolon'),
    )

    class Meta:
        fields = ['recipients', 'group_recipients', 'subject', 'text']

    def __init__(self, *args, **kwargs):
        """In PrivilegedMessageComposeForm the recipients field is not required."""
        super(PrivilegedMessageComposeForm, self).__init__(*args, **kwargs)
        self.surge_protection_timeout = None
        self.fields['recipients'].required = False

        # reorder the fields
        field_order = ['recipients', 'group_recipients', 'subject', 'text']
        fields = self.fields
        self.fields = OrderedDict((key, fields[key]) for key in field_order)
        # TODO: In django 1.9 this will be as easy as:
        # self.field_order = ['recipients', 'group_recipients', 'subject', 'text']

    def clean(self):
        """Join `recipients` and `group_recipients`."""
        super(PrivilegedMessageComposeForm, self).clean()

        cleaned_data = self.cleaned_data

        # Join recipients and group recipients lists
        recipients = set()
        recipients.update(cleaned_data.get('recipients', []))
        recipients.update(cleaned_data.get('group_recipients', []))
        cleaned_data['recipients'] = list(recipients)

        # If there are no recipients, show an error message.
        if len(recipients) == 0:
            raise forms.ValidationError(
                message=_(u'Please add a recipient.'),
                code='required',
            )

        return cleaned_data

    def clean_group_recipients(self):
        """Make sure the user is not in `group_recipients`."""
        group_recipients = self.cleaned_data['group_recipients']
        if self.user in group_recipients:
            group_recipients.remove(self.user)
        return group_recipients


class MultiMessageSelectForm(forms.Form):
    """Form to select messages to be archived or trashed."""
    CHOICE_ARCHIVE = 'archive'
    CHOICE_TRASH = 'trash'
    CHOICE_RESTORE = 'restore'
    ACTION_CHOICES = (
        (CHOICE_ARCHIVE, _(u'Archive')),
        (CHOICE_TRASH, _(u'Trash')),
        (CHOICE_RESTORE, _(u'Restore')),
    )

    selected_messages = forms.MultipleChoiceField(required=True)
    action = forms.ChoiceField(required=True, choices=ACTION_CHOICES)

    def __init__(self, *args, **kwargs):
        self.queryset = kwargs.pop('queryset')
        super(MultiMessageSelectForm, self).__init__(*args, **kwargs)
        self.fields['selected_messages'].choices = self.queryset.values_list('id', 'id')

    def clean_selected_messages(self):
        """Filter the queryset by the given selected_messages (ids) and return the queryset."""
        selected_messages = self.cleaned_data['selected_messages']
        return self.queryset.filter(pk__in=selected_messages)
