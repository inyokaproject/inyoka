# -*- coding: utf-8 -*-
"""
    inyoka.portal.forms
    ~~~~~~~~~~~~~~~~~~~

    Various forms for the portal.

    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import datetime
import Image
from django import forms
from django.forms import HiddenInput
from django.db.models import Count
from django.db.models import Count
from django.conf import settings
from django.core.validators import EMPTY_VALUES
from django.utils import simplejson
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from inyoka.forum.constants import SIMPLE_VERSION_CHOICES
from inyoka.forum.acl import filter_invisible
from inyoka.forum.models import Forum
from inyoka.utils.dates import datetime_to_timezone
from inyoka.utils.user import is_valid_username, normalize_username
from inyoka.utils.dates import TIMEZONES
from inyoka.utils.urls import href, is_safe_domain
from inyoka.utils.forms import CaptchaField, DateTimeWidget, \
                               HiddenCaptchaField, EmailField, JabberField
from inyoka.utils.local import current_request
from inyoka.utils.html import escape, cleanup_html
from inyoka.utils.storage import storage
from inyoka.utils.sessions import SurgeProtectionMixin
from inyoka.utils.search import search as search_system
from inyoka.portal.user import User, UserData, Group, ProfileField
from inyoka.portal.models import StaticPage, StaticFile
from inyoka.wiki.parser import validate_signature, SignatureError

#: Some constants used for ChoiceFields
NOTIFY_BY_CHOICES = (
    ('mail', _(u'Mail')),
    ('jabber', _(u'Jabber')),
)

NOTIFICATION_CHOICES = (
    ('topic_move', _(u'A subscribed topic was moved')),
    ('topic_split', _(u'A subscribed topic was splitted')),
    ('pm_new', _(u'I received a message'))
)

SEARCH_AREA_CHOICES = (
    ('all', _(u'Everywhere')),
    ('forum', _(u'Forum')),
    ('wiki', _(u'Wiki')),
    ('ikhaya', 'Ikhaya'),
    ('planet', _(u'Planet')),
)

SEARCH_SORT_CHOICES = (
    ('', 'Bereichsvorgabe verwenden'), #TODO: Bereichswas? Translation?
    ('date', _(u'Date')),
    ('relevance', _(u'Relevance')),
    ('magic', _(u'Date and relevance')),
)

DEFAULT_SEARCH_PARAMETER = 'magic'

SEARCH_AREAS = {
    'wiki': 'w',
    'forum': 'f',
    'ikhaya': 'i',
    'planet': 'p'
}


class LoginForm(forms.Form):
    """Simple form for the login dialog"""
    username = forms.CharField(label=_(u'Username, email address or openID'),
        widget=forms.TextInput(attrs={'tabindex': '1'}))
    password = forms.CharField(label=_(u'Password'), required=False,
        widget=forms.PasswordInput(render_value=False, attrs={'tabindex': '1'}),
        help_text=_(u'Leave this field empty if you are using openID.'),)
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
    username = forms.CharField(label=_(u'Username'))
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
    email = EmailField(label='E-Mail', help_text=_(u'We need your email '
        u'address to send you a new password if you forgot it. It is not '
        u'visible for other users. For more information, check out our '
        u'<a href="%(link)s">privacy police</a>.') % {'link': href('portal',
                                                             'datenschutz')})
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
                  u'alphanumeric chars and “-” and “ “ are allowed.')
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


class LostPasswordForm(forms.Form):
    """
    Form for the lost password form.

    It's similar to the register form and uses
    a hidden and a visible image CAPTCHA too.
    """
    username = forms.CharField(label=_('Username or email address'))
    captcha = CaptchaField(label=_('CAPTCHA'))
    hidden_captcha = HiddenCaptchaField(required=False)

    def clean_username(self):
        data = super(LostPasswordForm, self).clean()
        if 'username' in data and '@' in data['username']:
            try:
                self.user = User.objects.get(email=data['username'])
            except User.DoesNotExist:
                raise forms.ValidationError(
                    _(u'A user with the email address “%(mail)s“ does not exist.')
                    % {'mail': data['username']}
                )
        else:
            try:
                self.user = User.objects.get(data['username'])
            except User.DoesNotExist:
                raise forms.ValidationError(
                    _(u'The user “%(name)s“ does not exist.')
                    % {'name': data['username']}
                )


class SetNewPasswordForm(forms.Form):
    username = forms.CharField(widget=forms.HiddenInput)
    new_password_key = forms.CharField(widget=forms.HiddenInput)
    password = forms.CharField(label=_(u'New password'),
                               widget=forms.PasswordInput)
    password_confirm = forms.CharField(label=_(u'Confirm new password'),
                                       widget=forms.PasswordInput)

    def clean(self):
        data = super(SetNewPasswordForm, self).clean()
        if 'password' not in data or 'password_confirm' not in data or \
           data['password'] != data['password_confirm']:
            raise forms.ValidationError(u'Die Passwörter stimmen nicht '
                                        u'überein!')
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
    old_password = forms.CharField(label=_(u'Old password'),
                                   widget=forms.PasswordInput)
    new_password = forms.CharField(label=_(u'New password'),
                                   widget=forms.PasswordInput)
    new_password_confirm = forms.CharField(
                                   label=_(u'Confirm new password'),
                                   widget=forms.PasswordInput)


class UserCPSettingsForm(forms.Form):
    """
    Form used for the user control panel – dialog.
    """
    notify = forms.MultipleChoiceField(
        label=_(u'Notify via'), required=False,
        choices=NOTIFY_BY_CHOICES,
        widget=forms.CheckboxSelectMultiple)
    notifications = forms.MultipleChoiceField(
        label=_(u'Notify me if'), required=False,
        choices=NOTIFICATION_CHOICES,
        widget=forms.CheckboxSelectMultiple)
    ubuntu_version = forms.MultipleChoiceField(
        label='Benachrichtigung bei neuen Topics mit bestimmter Ubuntu Version',
        required=False, choices=SIMPLE_VERSION_CHOICES,
        widget=forms.CheckboxSelectMultiple)
    timezone = forms.ChoiceField(label=_(u'Timezone'), required=True,
        choices=zip(TIMEZONES, TIMEZONES))
    hide_profile = forms.BooleanField(label=_(u'Hide online status'),
                                      required=False)
    hide_avatars = forms.BooleanField(label=_(u'Hide avatars'),
                                      required=False)
    hide_signatures = forms.BooleanField(label=_(u'Hide signatures'),
                                         required=False)
    autosubscribe = forms.BooleanField(required=False,
                        label=_(u'Subscribe to a topic when replying'))
    show_preview = forms.BooleanField(required=False,
        label=_(u'Attachment preview'))
    show_thumbnails = forms.BooleanField(required=False,
        label=_(u'Picture preview'),
        help_text=_(u'No effect if “Attachment preview“ is disabled'))
    highlight_search = forms.BooleanField(required=False,
        label=_(u'Highlight search'))
    mark_read_on_logout = forms.BooleanField(required=False,
        label=_(u'Mark all forums as “read“ on logout'))


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

    avatar = forms.ImageField(label=_(u'Avatar'), required=False)
    delete_avatar = forms.BooleanField(label=_(u'Remove avatar'), required=False)
    use_gravatar = forms.BooleanField(label=_(u'Use Gravatar'), required=False)
    email = EmailField(label=_(u'Email'), required=True)
    jabber = JabberField(label=_(u'Jabber'), required=False)
    signature = forms.CharField(widget=forms.Textarea, label=_(u'Signature'),
                               required=False)
    coordinates = forms.CharField(label=_(u'Coordinates (latitude, longitude)'),
                                  required=False)

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
        try:
            validate_signature(signature)
        except SignatureError, exc:
            raise forms.ValidationError(exc.message)
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
                    u'“latitude, longitude“')
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
        Keep the user form setting avatar to a too big size.
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
            raise forms.ValidationError(_(u'This openID is already in use.'))
        return openid



class EditUserProfileForm(UserCPProfileForm):
    username = forms.CharField(label=_(u'Username'), max_length=30)
    member_title = forms.CharField(label=_(u'Title'), required=False)

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
                  u'alphanumeric chars and “-” and “ “ are allowed.')
            )
        if (self.user.username != username and
            User.objects.filter(username=username).exists()):
                raise forms.ValidationError(
                    _(u'A user with this name does already exist.')
                )
        return username


class UserCPAddProfileFieldForm(forms.Form):
    field = forms.ModelChoiceField(label=_(u'Field'),
                                   queryset=ProfileField.objects.all())
    data = forms.CharField(label=_(u'Data'))


class EditUserGroupsForm(forms.Form):
    primary_group = forms.CharField(label=_(u'Primary group'), required=False,
        help_text=_(u'Will be used for displaying the team icon'))


class CreateUserForm(forms.Form):
    username = forms.CharField(label=_(u'Username'), max_length=30)
    password = forms.CharField(label=_(u'Password'),
        widget=forms.PasswordInput(render_value=False))
    confirm_password = forms.CharField(label=_(u'Confirm password'),
        widget=forms.PasswordInput(render_value=False))
    email = EmailField(label=_(u'Email'))
    authenticate = forms.BooleanField(label=_(u'Authenticate'), initial=True,
        required=False, help_text=(_(u'The user will be send a confirmation '
            u'mail and set to “inactive“.')))

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
                  u'alphanumeric chars and “-” and “ “ are allowed.')
            )
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(
                u'Der Benutzername ist leider schon vergeben. '
                u'Bitte wähle einen anderen.')
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
    status = forms.ChoiceField(label=_(u'Activation status'), required=False,
                                   choices=enumerate([
                                       _(u'not yet activated'),
                                       _(u'active'),
                                       _(u'banned'),
                                       _(u'deleted himself'),
                                   ]))
    banned_until = forms.DateTimeField(label=_(u'Banned until'), required=False,
        widget=DateTimeWidget,
        help_text=_(u'leave empty to ban permanent'),
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
    new_password = forms.CharField(label=_(u'New password'),
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
    permissions = forms.MultipleChoiceField(label=u'Privilegien',
                                            required=False)


class UserMailForm(forms.Form):
    text = forms.CharField(label=u'Text',
        widget=forms.Textarea(),
        help_text=_(u'The message will be send as “plain text“. Your username '
                    u'will be noted as sender.')
    )


class EditGroupForm(forms.Form):
    name = forms.CharField(label=_(u'Group name'), max_length=80)
    is_public = forms.BooleanField(label=_(u'Public'), required=False)
    permissions = forms.MultipleChoiceField(label=_(u'Privileges'),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'permission'}),
        required=False)
    forum_privileges = forms.MultipleChoiceField(label=_(u'Forum privileges'),
                                                 required=False)
    icon = forms.ImageField(label=_(u'Team icon'), required=False)
    delete_icon = forms.BooleanField(label=_(u'Delete team icon'), required=False)
    import_icon_from_global = forms.BooleanField(label=_(u'Use global team icon'),
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
                    u'The groupname contains invalid chars'))
            if Group.objects.filter(name=name).exists():
                raise forms.ValidationError(_(
                    u'The groupname is not available. Please choose another one.'))
            return name
        else:
            raise forms.ValidationError(_(u'You need to enter a groupname'))


class SearchForm(forms.Form):
    """The search formular"""

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        forms.Form.__init__(self, *args, **kwargs)

        self.fields['forums'].choices = [('support', _(u'All support forums')),
            ('all', _(u'All forums'))]
        forums = filter_invisible(self.user, Forum.objects.get_cached())
        for offset, forum in Forum.get_children_recursive(forums):
            self.fields['forums'].choices.append((forum.slug, u'  ' * offset + forum.name))

    query = forms.CharField(label=_(u'Searchterms:'), widget=forms.TextInput)
    area = forms.ChoiceField(label=_(u'Area:'), choices=SEARCH_AREA_CHOICES,
                      required=False, widget=forms.RadioSelect, initial='all')
    page = forms.IntegerField(required=False, widget=forms.HiddenInput)
    per_page = forms.IntegerField(required=False, widget=forms.HiddenInput)
    date_begin = forms.DateTimeField(required=False, widget=DateTimeWidget)
    date_end = forms.DateTimeField(required=False, widget=DateTimeWidget)
    sort = forms.ChoiceField(label=_(u'Order by'), choices=SEARCH_SORT_CHOICES,
        required=False)
    forums = forms.ChoiceField(label=_(u'Forums'), initial='support',
        required=False)
    show_wiki_attachments = forms.BooleanField(label=_(u'Show attachments'),
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
    recipient = forms.CharField(label=_(u'To'), required=False,
        help_text=_(u'Separate multiple names by semicolon'))
    group_recipient = forms.CharField(label=_(u'Groups'), required=False,
        help_text=_(u'Separate multiple groups by semicolon'))
    subject = forms.CharField(label=_(u'Subject'),
                              widget=forms.TextInput(attrs={'size': 50}))
    text = forms.CharField(label=_(u'Message'), widget=forms.Textarea)

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
    title = forms.CharField(label=_(u'Short description'), max_length=50,
                            widget=forms.TextInput(attrs={'size':50}))
    text = forms.CharField(label=_(u'Long description'),
                           widget=forms.Textarea(attrs={'rows': 3}))
    url = forms.URLField(widget=forms.HiddenInput, required=False,
                         label=_(u'URL of the site the ticket refers to'))

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
                label=_(u'Number of entrys in the feed'),
                help_text=_(u'The number will be round off to keep the server '
                            u'load low.'))
    mode = forms.ChoiceField(initial='short',
        choices=(('full',  _(u'Full article')),
                 ('short', _(u'Only introduction')),
                 ('title', _(u'Only title'))),
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
    category = forms.ChoiceField(label=_(u'Category'))


class PlanetFeedSelectorForm(FeedSelectorForm):
    pass


class WikiFeedSelectorForm(FeedSelectorForm):
    #: `mode` is never used but needs to be overwritten because of that.
    mode = forms.ChoiceField(required=False)
    page = forms.CharField(label=_('Page name'), required=False,
                           help_text=(_(u'If not given, the last changes will '
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

    def save(self, commit=True):
        instance = super(EditFileForm, self).save(commit=False)
        instance.identifier = instance.file.name.rsplit('/', 1)[-1]
        if commit:
            instance.save()
        return instance


class ConfigurationForm(forms.Form):
    global_message = forms.CharField(label=_(u'Global Message'),
        widget=forms.Textarea(attrs={'rows': 3}), required=False,
        help_text = _(u'This message will displayed on every page in the '
                      u'header. To disable it, leave the field empty. '
                      u'Needs to be valid XHTML.'))
    blocked_hosts = forms.CharField(label=_(u'Blocked hosts for email addresses'),
        widget=forms.Textarea(attrs={'rows': 3}), required=False,
        help_text = _(u'Users cannot use email addresses from these hosts to '
                      u'register an account.'))
    team_icon = forms.ImageField(label=_(u'Global teamicon'), required=False,
        help_text=_(u'Please note the details on the maximum size below.'))
    max_avatar_width = forms.IntegerField(min_value=1)
    max_avatar_height = forms.IntegerField(min_value=1)
    max_avatar_size = forms.IntegerField(min_value=0)
    max_signature_length = forms.IntegerField(min_value=1,
        label=_(u'Maximum signature length'))
    max_signature_lines = forms.IntegerField(min_value=1,
        label=_(u'Maximum number of lines in signature'))
    get_ubuntu_link = forms.URLField(required=False,
        label=u'Der Downloadlink für die Startseite')
    get_ubuntu_description = forms.CharField(label=u'Beschreibung des Links')
    wiki_newpage_template = forms.CharField(required=False,
        widget=forms.Textarea(attrs={'rows': 5}),
        label=_(u'Default text of new wikipages'))
    wiki_newpage_root = forms.CharField(required=False,
        label=_(u'Location of new wikipages'))
    wiki_newpage_infopage = forms.CharField(required=False,
        label=_(u'Information page about new wikipages'),
        help_text=_(u'Information page to which a “create“ link should '
                    u'redirect to.'))
    team_icon_width = forms.IntegerField(min_value=1, required=False)
    team_icon_height = forms.IntegerField(min_value=1, required=False)
    license_note = forms.CharField(required=False, label=_(u'License note'),
                                   widget=forms.Textarea(attrs={'rows': 2}))
    distri_versions = forms.CharField(required=False, widget=HiddenInput())

    def clean_global_message(self):
        return cleanup_html(self.cleaned_data.get('global_message', ''))

    def clean_distri_versions(self):
        data = self.cleaned_data
        key = 'distri_versions'
        try:
            data[key] = data.get(key, '[]')
            # is there a way to validate a JSON string?
            simplejson.loads(data[key])
        except simplejson.JSONDecodeError:
            return u'[]'
        return data[key]


class EditProfileFieldForm(forms.Form):
    title = forms.CharField(label=_('Title'), required=True)

class EditStyleForm(forms.Form):
    styles = forms.CharField(label=_(u'Styles'), widget=forms.Textarea(
                             attrs={'rows': 20}), required=False)
