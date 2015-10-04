# -*- coding: utf-8 -*-
"""
    inyoka.portal.forms
    ~~~~~~~~~~~~~~~~~~~

    Various forms for the portal.

    :copyright: (c) 2007-2015 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import json
import StringIO
import datetime

from PIL import Image

from django import forms
from django.forms import HiddenInput
from django.contrib import messages
from django.db.models import Count
from django.core.cache import cache
from django.contrib.auth import forms as auth_forms
from django.core.files.base import ContentFile
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy
from django.core.files.storage import default_storage
from django.db.models.fields.files import ImageFieldFile

from inyoka.forum.constants import get_simple_version_choices
from inyoka.portal.models import StaticFile, StaticPage
from inyoka.portal.user import User, UserPage, Group, PERMISSION_NAMES, send_new_email_confirmation
from inyoka.utils.dates import TIMEZONES
from inyoka.utils.forms import (DateWidget, EmailField, CaptchaField,
    validate_signature)
from inyoka.utils.local import current_request
from inyoka.utils.urls import href
from inyoka.utils.user import is_valid_username, normalize_username
from inyoka.utils.sessions import SurgeProtectionMixin
from inyoka.utils.storage import storage


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


class LoginForm(forms.Form):
    """Simple form for the login dialog"""
    username = forms.CharField(label=ugettext_lazy(u'Username or email address'),
        widget=forms.TextInput(attrs={'tabindex': '1'}))
    password = forms.CharField(label=ugettext_lazy(u'Password'), required=False,
        widget=forms.PasswordInput(render_value=False, attrs={'tabindex': '1'}),)
    permanent = forms.BooleanField(label=_('Keep logged in'),
        required=False, widget=forms.CheckboxInput(attrs={'tabindex': '1'}))

    def clean(self):
        data = self.cleaned_data
        if 'username' in data and not (data['username'].startswith('http://') or
                data['username'].startswith('https://')) and data['password'] == '':
            msg = _(u'This field is required')
            self._errors['password'] = self.error_class([msg])
        return data


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
        u'<a href="%(link)s">privacy policy</a>.') % {
            'link': href('portal', 'datenschutz')})
    password = forms.CharField(label=_('Password'),
        widget=forms.PasswordInput(render_value=False))
    confirm_password = forms.CharField(label=_('Confirm password'),
        widget=forms.PasswordInput(render_value=False))
    captcha = CaptchaField(label=_('CAPTCHA'))
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
                  u'alphanumeric chars and “-” are allowed.')
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


class LostPasswordForm(auth_forms.PasswordResetForm):
    def save(self, **opts):
        request = opts['request']
        messages.success(request, _(u'An email with further instructions was sent to you.'))
        return super(LostPasswordForm, self).save(**opts)


class SetNewPasswordForm(auth_forms.SetPasswordForm):
    def save(self, commit=True):
        instance = super(SetNewPasswordForm, self).save(commit)
        messages.success(current_request,
            _(u'You successfully changed your password and are now '
              u'able to login.'))
        return instance


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
        required=False, widget=forms.CheckboxSelectMultiple)
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

    def __init__(self, *args, **kwargs):
        super(UserCPSettingsForm, self).__init__(*args, **kwargs)
        self.fields['ubuntu_version'].choices = get_simple_version_choices()

    def clean_notify(self):
        data = self.cleaned_data['notify']
        if u'jabber' in data:
            if not current_request.user.jabber:
                raise forms.ValidationError(mark_safe(_(u'You need to '
                    u'<a href="%(link)s">enter a valid jabber address</a> to '
                    u'use our jabber service.')
                    % {'link': href('portal', 'usercp', 'profile')}))
        return data


class UserCPProfileForm(forms.ModelForm):
    use_gravatar = forms.BooleanField(label=ugettext_lazy(u'Use Gravatar'), required=False)
    email = EmailField(label=ugettext_lazy(u'Email'), required=True)

    show_email = forms.BooleanField(required=False)
    show_jabber = forms.BooleanField(required=False)

    coordinates = forms.CharField(label=ugettext_lazy(u'Coordinates (latitude, longitude)'),
                                  required=False)
    gpgkey = forms.RegexField('^(0x)?[0-9a-f]+$(?i)',
        label=ugettext_lazy(u'GPG key'), max_length=255, required=False)

    userpage = forms.CharField(widget=forms.Textarea, required=False)

    class Meta:
        model = User
        fields = ['jabber', 'signature', 'location', 'website', 'gpgkey',
                  'launchpad', 'avatar']

    def __init__(self, *args, **kwargs):
        instance = kwargs['instance']
        self.admin_mode = kwargs.pop('admin_mode', False)
        initial = kwargs['initial'] = {}

        initial.update(dict(
            ((k, v) for k, v in instance.settings.iteritems()
             if k.startswith('show_'))
        ))
        initial['use_gravatar'] = instance.settings.get('use_gravatar', False)
        initial['email'] = instance.email
        if hasattr(instance, 'userpage'):
            initial['userpage'] = instance.userpage.content

        self.old_email = instance.email
        self.old_avatar = instance.avatar.name if instance.avatar else None
        self.change_avatar = False
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

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(
                _(u'This email address is already in use.'))
        return email

    def clean_avatar(self):
        """
        Keep the user from setting an avatar to a too big size.
        """
        avatar = self.cleaned_data['avatar']
        if avatar in (False, None):
            return avatar

        # FileField falls back to the initial value if no data is provided.
        # This happens when someone uploads a file larger than we do support,
        # or when the data does not change!
        if isinstance(avatar, ImageFieldFile):
            return

        # Resize the image if needed.
        image = Image.open(avatar)
        format = image.format
        max_size = (
            int(storage.get('max_avatar_width', 0)),
            int(storage.get('max_avatar_height', 0)))
        if any(length > max_length for max_length, length in zip(max_size, image.size)):
            image = image.resize(max_size)
        out = StringIO.StringIO()
        image.save(out, format)
        self.change_avatar = True
        return ContentFile(out.getvalue(), 'avatar.' + format.lower())

    def save(self, request, commit=True):
        data = self.cleaned_data
        user = super(UserCPProfileForm, self).save(commit=False)

        # Ensure that we delete the old avatar, otherwise Django will create
        # a file with a different name.
        if self.old_avatar and self.change_avatar:
            default_storage.delete(self.old_avatar)

        if self.admin_mode:
            user.email = data['email']
        else:
            if data['email'] != self.old_email:
                send_new_email_confirmation(user, data['email'])
                messages.info(request,
                    _(u'You’ve been sent an email to confirm your new email '
                      u'address.'))

        if data['userpage']:
            if hasattr(user, 'userpage'):
                userpage = user.userpage
            else:
                userpage = UserPage(user=user)
            userpage.content = data['userpage']
            userpage.content_rendered = ""
            if commit:
                userpage.save()
        else:
            if hasattr(user, 'userpage'):
                user.userpage.delete()

        if commit:
            user.save()
        return user


class EditUserProfileForm(UserCPProfileForm):
    class Meta(UserCPProfileForm.Meta):
        fields = UserCPProfileForm.Meta.fields + ['username', 'member_title']

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
                  u'alphanumeric chars and “-” are allowed.')
            )
        exists = User.objects.filter(username=username).exists()
        if (self.instance.username != username and exists):
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
                  u'alphanumeric chars and “-” are allowed.')
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


class EditUserStatusForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(EditUserStatusForm, self).__init__(*args, **kwargs)
        self.fields['banned_until'].localize = True

    class Meta:
        model = User
        fields = ['status', 'banned_until']

    def clean(self):
        """Keep the user from setting banned_until if status is not banned.
        """
        data = self.cleaned_data
        if not data.get('banned_until'):
            return data
        if int(data['status']) != 2:
            raise forms.ValidationError(_(u'The user is not banned'))
        if data['banned_until'] < datetime.datetime.utcnow():
            raise forms.ValidationError(_(u'The point of time is in the past.'))
        return data


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
                    u'will be noted as sender.'))


class EditGroupForm(forms.ModelForm):
    permissions = forms.MultipleChoiceField(label=ugettext_lazy(u'Privileges'),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'permission'}),
        required=False)
    forum_privileges = forms.MultipleChoiceField(label=ugettext_lazy(u'Forum privileges'),
                                                 required=False)
    import_icon_from_global = forms.BooleanField(label=ugettext_lazy(u'Use global team icon'),
        required=False)

    class Meta:
        model = Group
        fields = ('name', 'is_public', 'icon')
        widgets = {'icon': forms.ClearableFileInput}

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        initial = kwargs.setdefault('initial', {})
        if instance:
            initial['permissions'] = filter(lambda p: p & instance.permissions,
                                            PERMISSION_NAMES.keys())

        super(EditGroupForm, self).__init__(*args, **kwargs)
        self.fields['permissions'].choices = sorted(
            [(k, v) for k, v in PERMISSION_NAMES.iteritems()],
            key=lambda p: p[1]
        )

    def clean_name(self):
        """Validates that the name is alphanumeric"""
        data = self.cleaned_data
        try:
            name = normalize_username(data['name'])
        except ValueError:
            raise forms.ValidationError(_(
                u'The group name contains invalid chars'))
        return name

    def clean_import_icon_from_global(self):
        import_from_global = self.cleaned_data['import_icon_from_global']
        if import_from_global and not storage['team_icon']:
            raise forms.ValidationError(_(u'A global team icon was not yet defined.'))

    def save(self, commit=True):
        group = super(EditGroupForm, self).save(commit=False)
        data = self.cleaned_data

# TODO: Reenable?!
#        if data['icon'] and not data['import_icon_from_global']:
#            icon_resized = group.save_icon(data['icon'])
#            if icon_resized:
#                messages.info(request,
#                    _(u'The icon you uploaded was scaled to '
#                      '%(w)dx%(h)d pixels. Please note that this '
#                      'may result in lower quality.') % {
#                          'w': icon_mw,
#                          'h': icon_mh,
#                      })

        if data['import_icon_from_global']:
            if group.icon:
                group.icon.delete(save=False)

            icon_path = 'portal/team_icons/team_%s.%s' % (group.name,
                        storage['team_icon'].split('.')[-1])

            icon = default_storage.open(storage['team_icon'])
            group.icon.save(icon_path, icon)
            icon.close()

        # permissions
        permissions = 0
        for perm in data['permissions']:
            permissions |= int(perm)
        # clear permission cache of users if needed
        if permissions != group.permissions:
            group.permissions = permissions
            user_ids = User.objects.filter(groups=group).values_list('id', flat=True)
            keys = ['user_permissions/%s' % uid for uid in user_ids]
            cache.delete_many(keys)

        if commit:
            group.save()

        return group


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
    surge_protection_timeout = 60 * 5


class DeactivateUserForm(forms.Form):
    """Form for the user control panel -- deactivate_user view."""
    password_confirmation = forms.CharField(widget=forms.PasswordInput)


class SubscriptionForm(forms.Form):
    #: this is a list of integers of the subscriptions
    select = forms.MultipleChoiceField()


class PrivateMessageIndexForm(forms.Form):
    #: this is a list of integers of the pms that should get deleted
    delete = forms.MultipleChoiceField()


def _feed_count_cleanup(n):
    COUNTS = (10, 20, 30, 50)
    if n in COUNTS:
        return n
    if n < COUNTS[0]:
        return COUNTS[0]
    for i in range(len(COUNTS)):
        if n < COUNTS[i]:
            return n - COUNTS[i - 1] < COUNTS[i] - n and COUNTS[i - 1] or COUNTS[i]
    return COUNTS[-1]


class FeedSelectorForm(forms.Form):
    count = forms.IntegerField(initial=10,
                widget=forms.TextInput(attrs={'size': 2, 'maxlength': 3,
                                              'class': 'feed_count'}),
                label=ugettext_lazy(u'Number of entries in the feed'),
                help_text=ugettext_lazy(u'The number will be round off to keep the server '
                            u'load low.'))
    mode = forms.ChoiceField(initial='short',
        choices=(('full', ugettext_lazy(u'Full article')),
                 ('short', ugettext_lazy(u'Only introduction')),
                 ('title', ugettext_lazy(u'Only title'))),
        widget=forms.RadioSelect(attrs={'class': 'radioul'}))

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
        help_text=ugettext_lazy(u'This message will displayed on every page in the '
                      u'header. To disable it, leave the field empty.'))
    welcome_message = forms.CharField(label=ugettext_lazy(u'Welcome Message'),
        widget=forms.Textarea(attrs={'rows': 5}), required=False,
        help_text=ugettext_lazy('This is the welcome message displayed on the main page.'))
    blocked_hosts = forms.CharField(label=ugettext_lazy(u'Blocked hosts for email addresses'),
        widget=forms.Textarea(attrs={'rows': 5}), required=False,
        help_text=ugettext_lazy(u'Users cannot use email addresses from these hosts to '
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
    wiki_edit_note = forms.CharField(required=False,
        widget=forms.Textarea(attrs={'rows': 5}),
        label=ugettext_lazy(u'Wiki helptext'),
        help_text=ugettext_lazy(u'This text appears above the wiki editor.'))
    team_icon_width = forms.IntegerField(min_value=1, required=False)
    team_icon_height = forms.IntegerField(min_value=1, required=False)
    license_note = forms.CharField(required=False, label=ugettext_lazy(u'License note'),
                                   widget=forms.Textarea(attrs={'rows': 2}))
    countdown_active = forms.BooleanField(required=False,
        label=ugettext_lazy(u'Display countdown'))
    countdown_target_page = forms.CharField(required=False,
        label=ugettext_lazy(u'Full path to the target link page'))
    countdown_image_url = forms.CharField(required=False,
        label=ugettext_lazy(u'Image URL'),
        help_text=ugettext_lazy(u'The complete URL to the countdown banner. '
                    u'Use <code>%(remaining)s</code> to be replaced by the '
                    u'remaining days or <code>soon</code>.'))
    countdown_date = forms.DateField(label=ugettext_lazy(u'Release date'),
        required=False, widget=DateWidget, localize=True)
    distri_versions = forms.CharField(required=False, widget=HiddenInput())

    ikhaya_description = forms.CharField(required=False,
        widget=forms.Textarea(attrs={'rows': 5}),
        label=ugettext_lazy(u'Description about Ikhaya that will be used '
                            u'on the start page and in the feed aggregations.'))
    planet_description = forms.CharField(required=False,
        widget=forms.Textarea(attrs={'rows': 5}),
        label=ugettext_lazy(u'Description about the planet that will be used '
                            u'on the planet page and in the feed aggregations.'))

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

    def clean_countdown_image_url(self):
        data = self.cleaned_data.get('countdown_image_url', u'')
        try:
            data % {'remaining': 'soon'}
        except KeyError:
            raise forms.ValidationError(_(u'Invalid substitution pattern.'))
        return data


class EditStyleForm(forms.Form):
    styles = forms.CharField(label=ugettext_lazy(u'Styles'), widget=forms.Textarea(
                             attrs={'rows': 20}), required=False)
