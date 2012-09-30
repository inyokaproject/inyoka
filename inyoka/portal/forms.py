# -*- coding: utf-8 -*-
"""
    inyoka.portal.forms
    ~~~~~~~~~~~~~~~~~~~

    Various forms for the portal.

    :copyright: (c) 2007-2012 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import datetime
import json

from PIL import Image

from django import forms
from django.forms import HiddenInput
from django.db.models import Count
from django.conf import settings
from django.core.validators import EMPTY_VALUES
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy, ugettext as _

from django.contrib.auth.forms import PasswordResetForm

from inyoka.forum.constants import SIMPLE_VERSION_CHOICES
from inyoka.forum.acl import filter_invisible
from inyoka.forum.forms import ForumField
from inyoka.forum.models import Forum
from inyoka.utils.dates import datetime_to_timezone
from inyoka.utils.user import is_valid_username, normalize_username
from inyoka.utils.dates import TIMEZONES
from inyoka.utils.urls import href, is_safe_domain
from inyoka.utils.forms import CaptchaField, DateTimeWidget, \
    HiddenCaptchaField, EmailField, JabberField, validate_signature
from inyoka.utils.local import current_request
from inyoka.utils.html import cleanup_html
from inyoka.utils.storage import storage
from inyoka.utils.sessions import SurgeProtectionMixin
from inyoka.utils.search import search as search_system
from inyoka.portal.user import User, UserData, Group
from inyoka.portal.models import StaticPage, StaticFile

#: Some constants used for ChoiceFields
NOTIFY_BY_CHOICES = (
    ('mail', ugettext_lazy(u'Mail')),
    ('jabber', ugettext_lazy(u'Jabber')),
)

NOTIFICATION_CHOICES = (
    ('topic_move', ugettext_lazy(u'A subscribed topic was moved')),
    ('topic_split', ugettext_lazy(u'A subscribed topic was split')),
    ('pm_new', ugettext_lazy(u'I received a message'))
)

SEARCH_AREA_CHOICES = (
    ('all', ugettext_lazy(u'Everywhere')),
    ('forum', ugettext_lazy(u'Forum')),
    ('wiki', ugettext_lazy(u'Wiki')),
    ('ikhaya', 'Ikhaya'),
    ('planet', ugettext_lazy(u'Planet')),
)

SEARCH_SORT_CHOICES = (
    ('', ugettext_lazy(u'Use default value')),
    ('date', ugettext_lazy(u'Date')),
    ('relevance', ugettext_lazy(u'Relevance')),
    ('magic', ugettext_lazy(u'Date and relevance')),
)

FORUM_SEARCH_CHOICES = (
    ('support', ugettext_lazy(u'All support forums')),
    ('all', ugettext_lazy(u'All forums')))

DEFAULT_SEARCH_PARAMETER = 'magic'

SEARCH_AREAS = {
    'wiki': 'w',
    'forum': 'f',
    'ikhaya': 'i',
    'planet': 'p'
}


class LoginForm(forms.Form):
    """Simple form for the login dialog"""
    username = forms.CharField(label=ugettext_lazy(u'Username, email address or OpenID'),
        widget=forms.TextInput(attrs={'tabindex': '1'}))
    password = forms.CharField(label=ugettext_lazy(u'Password'), required=False,
        widget=forms.PasswordInput(render_value=False, attrs={'tabindex': '1'}),
        help_text=ugettext_lazy(u'Leave this field empty if you are using OpenID.'),)
    permanent = forms.BooleanField(label=_('Keep logged in'),
        required=False, widget=forms.CheckboxInput(attrs={'tabindex':'1'}))

    def clean(self):
        data = self.cleaned_data
        if 'username' in data and not (data['username'].startswith('http://') or \
         data['username'].startswith('https://')) and data['password'] == '':
            msg = _(u'This field is required')
            self._errors['password'] = self.error_class([msg])
        return data


class OpenIDConnectForm(forms.Form):
    username = forms.CharField(label=ugettext_lazy(u'Username'))
    password = forms.CharField(label=_('Password'),
        widget=forms.PasswordInput(render_value=False),
        required=True)


class RegisterForm(forms.Form):
    """
    Form for registering a new user account.

    Validates that the requested username is not already in use, and
    requires the password to be entered twice to catch typos.
    The user also needs to confirm our terms of usage and there are some
    techniques for bot catching included e.g a CAPTCHA and a hidden captcha
    for bots that just fill out everything.
    """
    username = forms.CharField(label=_('Username'), max_length=20)
    email = EmailField(label=ugettext_lazy(u'E-mail'),
        help_text=ugettext_lazy(u'We need your email '
        u'address to send you a new password if you forgot it. It is not '
        u'visible to other users. For more information, check out our '
        u'<a href="%(link)s">privacy police</a>.') % {
            'link': href('portal', 'datenschutz')})
    password = forms.CharField(label=_('Password'),
        widget=forms.PasswordInput(render_value=False))
    confirm_password = forms.CharField(label=_('Confirm password'),
        widget=forms.PasswordInput(render_value=False))
    captcha = CaptchaField(label=_('CAPTCHA'))
    hidden_captcha = HiddenCaptchaField(required=False)
    terms_of_usage = forms.BooleanField()

    def clean_username(self):
        """
        Validates that the username is alphanumeric and is not already
        in use.
        """
        username = self.cleaned_data['username']
        if not is_valid_username(username):
            raise forms.ValidationError(
                _(u'Your username contains invalid characters. Only '
                  u'alphanumeric chars and “-” and “ ” are allowed.')
            )
        try:
            User.objects.get(username)
        except User.DoesNotExist:
            # To bad we had to change the user regex…,  we need to rename users fast…
            count = User.objects.filter(username__contains=username.replace(' ', '%')) \
                                .aggregate(user_count=Count('username'))['user_count']
            if count == 0:
                return username

        raise forms.ValidationError(
            _(u'This username is not available, please try another one.')
        )

    def clean(self):
        """
        Validates that the two password inputs match.
        """
        if 'password' in self.cleaned_data and 'confirm_password' in self.cleaned_data:
            if self.cleaned_data['password'] == self.cleaned_data['confirm_password']:
                return self.cleaned_data
            raise forms.ValidationError(
                _(u'The password must match the password confirmation.')
            )
        else:
            raise forms.ValidationError(
                _(u'You need to enter a password and a password confirmation.')
            )

    def clean_terms_of_usage(self):
        """Validates that the user agrees our terms of usage"""
        if self.cleaned_data.get('terms_of_usage', False):
            return True
        raise forms.ValidationError(
            _(u'You need to read and accept our terms and conditions.')
        )

    def clean_email(self):
        """
        Validates if the required field `email` contains
        a non existing mail address.
        """
        exists = User.objects.filter(email__iexact=self.cleaned_data['email'])\
                             .exists()
        if exists:
            raise forms.ValidationError(mark_safe(
                _(u'The given email address is already in use. If you forgot '
                  u'your password, you can <a href="%(link)s">restore it</a>.')
                % {'link': href('portal', 'lost_password')}))
        return self.cleaned_data['email']


class LostPasswordForm(PasswordResetForm):
    def save(self, **opts):
        request = opts['request']
        messages.success(request, _(u'An email with further instructions was sent to you.'))
        return super(PasswordResetForm, self).save(**opts)


class SetNewPasswordForm(forms.Form):
    username = forms.CharField(widget=forms.HiddenInput)
    new_password_key = forms.CharField(widget=forms.HiddenInput)
    password = forms.CharField(label=ugettext_lazy(u'New password'),
                               widget=forms.PasswordInput)
    password_confirm = forms.CharField(label=ugettext_lazy(u'Confirm new password'),
                                       widget=forms.PasswordInput)

    def clean(self):
        data = super(SetNewPasswordForm, self).clean()
        if 'password' not in data or 'password_confirm' not in data or \
           data['password'] != data['password_confirm']:
            raise forms.ValidationError(_(u'The passwords do not match!'))
        try:
            data['user'] = User.objects.get(self['username'].data,
                               new_password_key=self['new_password_key'].data)
        except User.DoesNotExist:
            raise forms.ValidationError(_(
                u'The user does not exist or the confirmation key is invalid')
            )
        return data


class ChangePasswordForm(forms.Form):
    """Simple form for changing the password."""
    old_password = forms.CharField(label=ugettext_lazy(u'Old password'),
                                   widget=forms.PasswordInput)
    new_password = forms.CharField(label=ugettext_lazy(u'New password'),
                                   widget=forms.PasswordInput)
    new_password_confirm = forms.CharField(
                                   label=ugettext_lazy(u'Confirm new password'),
                                   widget=forms.PasswordInput)


class UserCPSettingsForm(forms.Form):
    """
    Form used for the user control panel – dialog.
    """
    notify = forms.MultipleChoiceField(
        label=ugettext_lazy(u'Notify via'), required=False,
        choices=NOTIFY_BY_CHOICES,
        widget=forms.CheckboxSelectMultiple)
    notifications = forms.MultipleChoiceField(
        label=ugettext_lazy(u'Notify me if'), required=False,
        choices=NOTIFICATION_CHOICES,
        widget=forms.CheckboxSelectMultiple)
    ubuntu_version = forms.MultipleChoiceField(
        label=ugettext_lazy(u'Notifications on topics with a specific Ubuntu version'),
        required=False, choices=SIMPLE_VERSION_CHOICES,
        widget=forms.CheckboxSelectMultiple)
    timezone = forms.ChoiceField(label=ugettext_lazy(u'Timezone'), required=True,
        choices=zip(TIMEZONES, TIMEZONES))
    hide_profile = forms.BooleanField(label=ugettext_lazy(u'Hide online status'),
                                      required=False)
    hide_avatars = forms.BooleanField(label=ugettext_lazy(u'Hide avatars'),
                                      required=False)
    hide_signatures = forms.BooleanField(label=ugettext_lazy(u'Hide signatures'),
                                         required=False)
    autosubscribe = forms.BooleanField(required=False,
                        label=ugettext_lazy(u'Subscribe to a topic when replying'))
    show_preview = forms.BooleanField(required=False,
        label=ugettext_lazy(u'Attachment preview'))
    show_thumbnails = forms.BooleanField(required=False,
        label=ugettext_lazy(u'Picture preview'),
        help_text=ugettext_lazy(u'No effect if “attachment preview” is disabled'))
    highlight_search = forms.BooleanField(required=False,
        label=ugettext_lazy(u'Highlight search'))
    mark_read_on_logout = forms.BooleanField(required=False,
        label=ugettext_lazy(u'Mark all forums as “read” on logout'))


    def clean_notify(self):
        data = self.cleaned_data['notify']
        if u'jabber' in data:
            if not current_request.user.jabber:
                raise forms.ValidationError(mark_safe(_(u'You need to '
                    u'<a href="%(link)s"> enter a valid jabber address</a> to '
                    u'use our jabber service.')
                    % {'link': href('portal', 'usercp', 'profile')}))
        return data


class UserCPProfileForm(forms.Form):

    avatar = forms.ImageField(label=ugettext_lazy(u'Avatar'), required=False)
    delete_avatar = forms.BooleanField(label=ugettext_lazy(u'Remove avatar'), required=False)
    use_gravatar = forms.BooleanField(label=ugettext_lazy(u'Use Gravatar'), required=False)
    email = EmailField(label=ugettext_lazy(u'Email'), required=True)
    jabber = JabberField(label=ugettext_lazy(u'Jabber'), required=False)
    icq = forms.IntegerField(label=ugettext_lazy(u'ICQ'), required=False,
                             min_value=1, max_value=1000000000)
    msn = forms.CharField(label=ugettext_lazy(u'MSN'), required=False)
    aim = forms.CharField(label=ugettext_lazy(u'AIM'), required=False, max_length=25)
    yim = forms.CharField(label=ugettext_lazy(u'Yahoo Messenger'), required=False,
                         max_length=25)
    skype = forms.CharField(label=ugettext_lazy(u'Skype'), required=False, max_length=25)
    wengophone = forms.CharField(label=ugettext_lazy(u'WengoPhone'), required=False,
                                 max_length=25)
    sip = forms.CharField(label=ugettext_lazy(u'SIP'), required=False, max_length=25)
    show_email = forms.BooleanField(required=False)
    show_jabber = forms.BooleanField(required=False)
    signature = forms.CharField(widget=forms.Textarea, label=ugettext_lazy(u'Signature'),
                               required=False)
    coordinates = forms.CharField(label=ugettext_lazy(u'Coordinates (latitude, longitude)'),
                                  required=False)
    location = forms.CharField(label=ugettext_lazy(u'Residence'), required=False, max_length=50)
    occupation = forms.CharField(label=ugettext_lazy(u'Job'), required=False, max_length=50)
    interests = forms.CharField(label=ugettext_lazy(u'Interests'), required=False,
                                max_length=100)
    website = forms.URLField(label=ugettext_lazy(u'Website'), required=False)
    launchpad = forms.CharField(label=ugettext_lazy(u'Launchpad username'), required=False,
                                max_length=50)
    gpgkey = forms.RegexField('^(0x)?[0-9a-f]+$(?i)',
        label=ugettext_lazy(u'GPG key'), max_length=255, required=False)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(UserCPProfileForm, self).__init__(*args, **kwargs)

    def clean_gpgkey(self):
        gpgkey = self.cleaned_data.get('gpgkey', '').upper()
        if gpgkey.startswith('0X'):
            gpgkey = gpgkey[2:]
        return gpgkey

    def clean_signature(self):
        signature = self.cleaned_data.get('signature', '')
        validate_signature(signature)
        return signature

    def clean_coordinates(self):
        coords = self.cleaned_data.get('coordinates', '').strip()
        if not coords:
            return None
        try:
            coords = [float(x.strip()) for x in coords.split(',')]
            if len(coords) != 2:
                raise forms.ValidationError(_(
                    u'Coordinates needs to be passed in the format '
                    u'“latitude, longitude”')
                )
            lat, long = coords
        except ValueError:
            raise forms.ValidationError(_(u'Coordinates needs to decimal numbers.'))
        if not -90 < lat < 90:
            raise forms.ValidationError(_(u'Latitude needs to be between -90 and 90.'))
        if not -180 < long < 180:
            raise forms.ValidationError(_(u'Longitude needs to be between -180 and 180.'))
        return lat, long

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip()
        if not email:
            raise forms.ValidationError(_(u'You entered no email address.'))
        try:
            other_user = User.objects.get(email=email)
        except User.DoesNotExist:
            return email
        else:
            if other_user.id != self.user.id:
                raise forms.ValidationError(_(u'This email address is already in use.'))
            return email

    def clean_avatar(self):
        """
        Keep the user from setting an avatar to a too big size.
        """
        data = self.cleaned_data
        if data['avatar'] is None:
            return
        if data['avatar'] is False:
            return False

        st = int(storage.get('max_avatar_size', 0))
        if st and data['avatar'].size > st * 1024:
            raise forms.ValidationError(
                _(u'The chosen avatar could not be uploaded, it is to large. '
                  u'Please choose another avatar.')
            )
        try:
            image = Image.open(data['avatar'])
        finally:
            data['avatar'].seek(0)
        max_size = (
            int(storage.get('max_avatar_width', 0)),
            int(storage.get('max_avatar_height', 0)))
        if any(length > max_length for max_length, length in zip(max_size, image.size)):
            raise forms.ValidationError(
                _(u'The chosen avatar could not be uploaded, it is to large. '
                  u'Please choose another avatar.')
            )
        return data['avatar']

    def clean_openid(self):
        if self.cleaned_data['openid'] in EMPTY_VALUES:
            return
        openid = self.cleaned_data['openid']
        if UserData.objects.filter(key='openid', value=openid)\
                           .exclude(user=self.user).count():
            raise forms.ValidationError(_(u'This OpenID is already in use.'))
        return openid



class EditUserProfileForm(UserCPProfileForm):
    username = forms.CharField(label=ugettext_lazy(u'Username'), max_length=30)
    member_title = forms.CharField(label=ugettext_lazy(u'Title'), required=False)

    def clean_username(self):
        """
        Validates that the username is alphanumeric and is not already
        in use.
        """
        data = self.cleaned_data
        username = data['username']
        if not is_valid_username(username):
            raise forms.ValidationError(
                _(u'Your username contains invalid characters. Only '
                  u'alphanumeric chars and “-” and “ ” are allowed.')
            )
        exists = User.objects.filter(username=username).exists()
        if (self.user.username != username and exists):
            raise forms.ValidationError(
                _(u'A user with this name already exists.'))
        return username


class EditUserGroupsForm(forms.Form):
    primary_group = forms.CharField(label=ugettext_lazy(u'Primary group'), required=False,
        help_text=ugettext_lazy(u'Will be used to display the team icon'))


class CreateUserForm(forms.Form):
    username = forms.CharField(label=ugettext_lazy(u'Username'), max_length=30)
    password = forms.CharField(label=ugettext_lazy(u'Password'),
        widget=forms.PasswordInput(render_value=False))
    confirm_password = forms.CharField(label=ugettext_lazy(u'Confirm password'),
        widget=forms.PasswordInput(render_value=False))
    email = EmailField(label=ugettext_lazy(u'Email'))
    authenticate = forms.BooleanField(label=ugettext_lazy(u'Authenticate'), initial=True,
        required=False, help_text=(ugettext_lazy(u'The user will be send a confirmation '
            u'mail and set to “inactive”.')))

    def clean_username(self):
        """
        Validates that the username is alphanumeric and is not already
        in use.
        """
        data = self.cleaned_data
        username = data['username']
        if not is_valid_username(username):
            raise forms.ValidationError(
                _(u'Your username contains invalid characters. Only '
                  u'alphanumeric chars and “-” and “ ” are allowed.')
            )
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(
                _(u'The username is already in use. Please choose another one.'))
        return username

    def clean_confirm_password(self):
        """
        Validates that the two password inputs match.
        """
        data = self.cleaned_data
        if 'password' in data and 'confirm_password' in data:
            if data['password'] == data['confirm_password']:
                return data['confirm_password']
            raise forms.ValidationError(
                _(u'The password must match the password confirmation.')
            )
        else:
            raise forms.ValidationError(
                _(u'You need to enter a password and a password confirmation.')
            )

    def clean_email(self):
        """
        Validates if the required field `email` contains
        a non existing mail address.
        """
        if 'email' in self.cleaned_data:
            if User.objects.filter(email=self.cleaned_data['email']).exists():
                raise forms.ValidationError(_(u'This email address is already in use.'))
            return self.cleaned_data['email']
        else:
            raise forms.ValidationError(_(u'You need to enter a email address'))


class EditUserStatusForm(forms.Form):
    status = forms.ChoiceField(label=ugettext_lazy(u'Activation status'),
                               required=False,
                               choices=enumerate([
                                   ugettext_lazy(u'not yet activated'),
                                   ugettext_lazy(u'active'),
                                   ugettext_lazy(u'banned'),
                                   ugettext_lazy(u'deleted himself')]))
    banned_until = forms.DateTimeField(label=ugettext_lazy(u'Banned until'), required=False,
        widget=DateTimeWidget,
        help_text=ugettext_lazy(u'leave empty to ban permanent'),
        localize=True)

    def clean_banned_until(self):
        """
        Keep the user from setting banned_until if status is not banned.
        This is to avoid confusion because this was previously possible.
        """
        data = self.cleaned_data
        if data['banned_until'] is None:
            return
        if data['status'] not in (2, '2'):
            raise forms.ValidationError(
                _(u'The user is not banned')
            )
        if data['banned_until'] < datetime.datetime.utcnow():
            raise forms.ValidationError(
                _(u'The point of time is in the past.')
            )
        return data['banned_until']


class EditUserPasswordForm(forms.Form):
    new_password = forms.CharField(label=ugettext_lazy(u'New password'),
        required=False, widget=forms.PasswordInput(render_value=False))
    confirm_password = forms.CharField(label=_('Confirm new password'),
        required=False, widget=forms.PasswordInput(render_value=False))

    def clean_confirm_password(self):
        """
        Validates that the two password inputs match.
        """
        data = self.cleaned_data
        if 'new_password' in data and 'confirm_password' in data:
            if data['new_password'] == data['confirm_password']:
                return data['confirm_password']
            raise forms.ValidationError(
                _(u'The password must match the password confirmation.')
            )
        else:
            raise forms.ValidationError(
                _(u'You need to enter a password and a password confirmation.')
            )


class EditUserPrivilegesForm(forms.Form):
    permissions = forms.MultipleChoiceField(label=ugettext_lazy(u'Privileges'),
                                            required=False)


class UserMailForm(forms.Form):
    text = forms.CharField(label=ugettext_lazy(u'Text'),
        widget=forms.Textarea(),
        help_text=ugettext_lazy(u'The message will be send as “plain text”. Your username '
                    u'will be noted as sender.')
    )


class EditGroupForm(forms.Form):
    name = forms.CharField(label=ugettext_lazy(u'Group name'), max_length=80)
    is_public = forms.BooleanField(label=ugettext_lazy(u'Public'), required=False)
    permissions = forms.MultipleChoiceField(label=ugettext_lazy(u'Privileges'),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'permission'}),
        required=False)
    forum_privileges = forms.MultipleChoiceField(label=ugettext_lazy(u'Forum privileges'),
                                                 required=False)
    icon = forms.ImageField(label=ugettext_lazy(u'Team icon'), required=False)
    delete_icon = forms.BooleanField(label=ugettext_lazy(u'Delete team icon'), required=False)
    import_icon_from_global = forms.BooleanField(label=ugettext_lazy(u'Use global team icon'),
        required=False)


class CreateGroupForm(EditGroupForm):

    def clean_name(self):
        """Validates that the name is alphanumeric and is not already in use."""

        data = self.cleaned_data
        if 'name' in data:
            try:
                name = normalize_username(data['name'])
            except ValueError:
                raise forms.ValidationError(_(
                    u'The group name contains invalid chars'))
            if Group.objects.filter(name=name).exists():
                raise forms.ValidationError(_(
                    u'The group name is not available. Please choose another one.'))
            return name
        else:
            raise forms.ValidationError(_(u'You need to enter a group name'))


class SearchForm(forms.Form):
    """The search formular"""

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        forms.Form.__init__(self, *args, **kwargs)

        self.fields['forums'].choices = FORUM_SEARCH_CHOICES
        forums = filter_invisible(self.user, Forum.objects.get_cached())
        for offset, forum in Forum.get_children_recursive(forums):
            self.fields['forums'].choices.append((forum.slug, u'  ' * offset + forum.name))

    query = forms.CharField(label=ugettext_lazy(u'Search terms:'), widget=forms.TextInput)
    area = forms.ChoiceField(label=ugettext_lazy(u'Area:'), choices=SEARCH_AREA_CHOICES,
                      required=False, widget=forms.RadioSelect, initial='all')
    page = forms.IntegerField(required=False, widget=forms.HiddenInput)
    per_page = forms.IntegerField(required=False, widget=forms.HiddenInput)
    date_begin = forms.DateTimeField(required=False, widget=DateTimeWidget)
    date_end = forms.DateTimeField(required=False, widget=DateTimeWidget)
    sort = forms.ChoiceField(label=ugettext_lazy(u'Order by'), choices=SEARCH_SORT_CHOICES,
        required=False)
    forums = ForumField(label=ugettext_lazy(u'Forums'), initial='support',
        required=False)
    show_wiki_attachments = forms.BooleanField(label=ugettext_lazy(u'Show attachments'),
        required=False)

    def clean(self):
        # Default search order depends on the search area.
        cleaned_data = forms.Form.clean(self)
        cleaned_data['area'] = (cleaned_data.get('area') or 'all').lower()
        if not cleaned_data.get('sort'):
            if cleaned_data['area'] == 'wiki':
                cleaned_data['sort'] = 'relevance'
            else:
                cleaned_data['sort'] = DEFAULT_SEARCH_PARAMETER
        return cleaned_data

    def search(self):
        """Performs the actual query and return the results"""
        d = self.cleaned_data

        query = d['query']

        exclude = []

        # we use per default the support-forum filter
        if not d['forums']:
            d['forums'] = 'support'

        if d['area'] in ('forum', 'all') and d['forums'] and \
                d['forums'] not in ('support', 'all'):
            query += ' category:"%s"' % d['forums']
        elif d['forums'] == 'support':
            exclude = list(settings.SEARCH_DEFAULT_EXCLUDE)

        if not d['show_wiki_attachments']:
            exclude.append('C__attachment__')

        return search_system.query(self.user,
            query,
            page=d['page'] or 1,
            per_page=d['per_page'] or 20,
            date_begin=datetime_to_timezone(d['date_begin'], enforce_utc=True),
            date_end=datetime_to_timezone(d['date_end'], enforce_utc=True),
            component=SEARCH_AREAS.get(d['area']),
            exclude=exclude,
            sort=d['sort'] or DEFAULT_SEARCH_PARAMETER
        )



class PrivateMessageForm(forms.Form):
    """Form for writing a new private message"""
    recipient = forms.CharField(label=ugettext_lazy(u'To'), required=False,
        help_text=ugettext_lazy(u'Separate multiple names by semicolon'))
    group_recipient = forms.CharField(label=ugettext_lazy(u'Groups'), required=False,
        help_text=ugettext_lazy(u'Separate multiple groups by semicolon'))
    subject = forms.CharField(label=ugettext_lazy(u'Subject'),
                              widget=forms.TextInput(attrs={'size': 50}))
    text = forms.CharField(label=ugettext_lazy(u'Message'), widget=forms.Textarea)

    def clean(self):
        d = self.cleaned_data
        if 'recipient' in d and 'group_recipient' in d:
            if not d['recipient'].strip() and not d['group_recipient'].strip():
                raise forms.ValidationError(_(u'Please enter at least one receiver.'))
        return self.cleaned_data

class PrivateMessageFormProtected(SurgeProtectionMixin, PrivateMessageForm):
    source_protection_timeout = 60 * 5


class DeactivateUserForm(forms.Form):
    """Form for the user control panel -- deactivate_user view."""
    password_confirmation = forms.CharField(widget=forms.PasswordInput)


class SubscriptionForm(forms.Form):
    #: this is a list of integers of the subscriptions
    select = forms.MultipleChoiceField()


class PrivateMessageIndexForm(forms.Form):
    #: this is a list of integers of the pms that should get deleted
    delete = forms.MultipleChoiceField()


class UserErrorReportForm(forms.Form):
    title = forms.CharField(label=ugettext_lazy(u'Short description'), max_length=50,
                            widget=forms.TextInput(attrs={'size':50}))
    text = forms.CharField(label=ugettext_lazy(u'Long description'),
                           widget=forms.Textarea(attrs={'rows': 3}))
    url = forms.URLField(widget=forms.HiddenInput, required=False,
                         label=ugettext_lazy(u'URL of the site the ticket refers to'))

    def clean_url(self):
        data = self.cleaned_data
        if data.get('url') and not is_safe_domain(self.cleaned_data['url']):
            raise forms.ValidationError(_(u'Invalid URL'))
        return self.cleaned_data['url']


def _feed_count_cleanup(n):
    COUNTS = (10, 20, 30, 50)
    if n in COUNTS:
        return n
    if n < COUNTS[0]:
        return COUNTS[0]
    for i in range(len(COUNTS)):
        if n < COUNTS[i]:
            return n - COUNTS[i-1] < COUNTS[i] - n and COUNTS[i-1] or COUNTS[i]
    return COUNTS[-1]


class FeedSelectorForm(forms.Form):
    count = forms.IntegerField(initial=10,
                widget=forms.TextInput(attrs={'size': 2, 'maxlength': 3,
                                              'class': 'feed_count'}),
                label=ugettext_lazy(u'Number of entries in the feed'),
                help_text=ugettext_lazy(u'The number will be round off to keep the server '
                            u'load low.'))
    mode = forms.ChoiceField(initial='short',
        choices=(('full',  ugettext_lazy(u'Full article')),
                 ('short', ugettext_lazy(u'Only introduction')),
                 ('title', ugettext_lazy(u'Only title'))),
        widget=forms.RadioSelect(attrs={'class':'radioul'}))

    def clean(self):
        data = self.cleaned_data
        data['count'] = _feed_count_cleanup(data.get('count', 20))
        return data


class ForumFeedSelectorForm(FeedSelectorForm):
    component = forms.ChoiceField(initial='forum',
        choices=(('*', u''), ('forum', u''), ('topic', u'')))
    forum = forms.ChoiceField(required=False)

    def clean_forum(self):
        data = self.cleaned_data
        if data.get('component') == 'forum' and not data.get('forum'):
            raise forms.ValidationError(_(u'Please select a forum'))
        return data['forum']


class IkhayaFeedSelectorForm(FeedSelectorForm):
    category = forms.ChoiceField(label=ugettext_lazy(u'Category'))


class PlanetFeedSelectorForm(FeedSelectorForm):
    pass


class WikiFeedSelectorForm(FeedSelectorForm):
    #: `mode` is never used but needs to be overwritten because of that.
    mode = forms.ChoiceField(required=False)
    page = forms.CharField(label=_('Page name'), required=False,
                           help_text=(ugettext_lazy(u'If not given, the last changes will '
                                        u'be displayed.')))


class EditStaticPageForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(EditStaticPageForm, self).__init__(*args, **kwargs)
        self.fields['key'].required = False

    class Meta:
        model = StaticPage


class EditFileForm(forms.ModelForm):
    class Meta:
        model = StaticFile
        exclude = ['identifier']

    def clean_file(self):
        data = self.cleaned_data
        if 'file' in data and StaticFile.objects.filter(
                identifier=data['file']).exists():
            raise forms.ValidationError(_(u'Another file with this name '
                u'already exists. Please edit this file.'))
        return data['file']

    def save(self, commit=True):
        instance = super(EditFileForm, self).save(commit=False)
        instance.identifier = instance.file.name.rsplit('/', 1)[-1]
        if commit:
            instance.save()
        return instance


class ConfigurationForm(forms.Form):
    global_message = forms.CharField(label=ugettext_lazy(u'Global Message'),
        widget=forms.Textarea(attrs={'rows': 3}), required=False,
        help_text = ugettext_lazy(u'This message will displayed on every page in the '
                      u'header. To disable it, leave the field empty. '
                      u'Needs to be valid XHTML.'))
    blocked_hosts = forms.CharField(label=ugettext_lazy(u'Blocked hosts for email addresses'),
        widget=forms.Textarea(attrs={'rows': 3}), required=False,
        help_text = ugettext_lazy(u'Users cannot use email addresses from these hosts to '
                      u'register an account.'))
    team_icon = forms.ImageField(label=ugettext_lazy(u'Global team icon'), required=False,
        help_text=ugettext_lazy(u'Please note the details on the maximum size below.'))
    max_avatar_width = forms.IntegerField(min_value=1)
    max_avatar_height = forms.IntegerField(min_value=1)
    max_avatar_size = forms.IntegerField(min_value=0)
    max_signature_length = forms.IntegerField(min_value=1,
        label=ugettext_lazy(u'Maximum signature length'))
    max_signature_lines = forms.IntegerField(min_value=1,
        label=ugettext_lazy(u'Maximum number of lines in signature'))
    get_ubuntu_link = forms.URLField(required=False,
        label=ugettext_lazy(u'The download link for the start page'))
    get_ubuntu_description = forms.CharField(label=ugettext_lazy(u'Description of the link'))
    wiki_newpage_template = forms.CharField(required=False,
        widget=forms.Textarea(attrs={'rows': 5}),
        label=ugettext_lazy(u'Default text of new wiki pages'))
    wiki_newpage_root = forms.CharField(required=False,
        label=ugettext_lazy(u'Location of new wiki pages'))
    wiki_newpage_infopage = forms.CharField(required=False,
        label=ugettext_lazy(u'Information page about new wiki pages'),
        help_text=ugettext_lazy(u'Information page to which a “create” link should '
                    u'redirect to.'))
    team_icon_width = forms.IntegerField(min_value=1, required=False)
    team_icon_height = forms.IntegerField(min_value=1, required=False)
    license_note = forms.CharField(required=False, label=ugettext_lazy(u'License note'),
                                   widget=forms.Textarea(attrs={'rows': 2}))
    distri_versions = forms.CharField(required=False, widget=HiddenInput())

    ikhaya_description = forms.CharField(required=False,
        widget=forms.Textarea(attrs={'rows': 3}),
        label=ugettext_lazy(u'Description about Ikhaya that will be used '
                            u'on the start page and in the feed aggregations.'))
    planet_description = forms.CharField(required=False,
        widget=forms.Textarea(attrs={'rows': 3}),
        label=ugettext_lazy(u'Description about the planet that will be used '
                            u'in the feed aggregations.'))

    def clean_global_message(self):
        return cleanup_html(self.cleaned_data.get('global_message', ''))

    def clean_distri_versions(self):
        data = self.cleaned_data
        key = 'distri_versions'
        try:
            data[key] = data.get(key, '[]')
            # is there a way to validate a JSON string?
            json.loads(data[key])
        except ValueError:
            return u'[]'
        return data[key]


class EditStyleForm(forms.Form):
    styles = forms.CharField(label=ugettext_lazy(u'Styles'), widget=forms.Textarea(
                             attrs={'rows': 20}), required=False)
