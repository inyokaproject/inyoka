"""
    inyoka.portal.forms
    ~~~~~~~~~~~~~~~~~~~

    Various forms for the portal.

    :copyright: (c) 2007-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import functools
import io
import json
import os

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import forms as auth_forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import Group, Permission
from django.core import signing, validators
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.validators import validate_email
from django.db.models import CharField, Value
from django.db.models.fields.files import ImageFieldFile
from django.db.models.functions import Concat
from django.forms import HiddenInput, modelformset_factory, SplitDateTimeField
from django.utils import timezone as dj_timezone
from django.utils.html import format_html
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from guardian.shortcuts import assign_perm, get_perms, remove_perm
from PIL import Image

from inyoka.forum.constants import get_simple_version_choices
from inyoka.forum.models import Forum
from inyoka.portal.models import Linkmap, StaticFile, StaticPage
from inyoka.portal.user import (
    User,
    UserBanned,
    UserPage,
    reactivate_user,
    reset_email,
    send_new_email_confirmation,
    set_new_email,
)
from inyoka.utils.dates import TIMEZONES
from inyoka.utils.forms import (
    CaptchaField,
    EmailField,
    ForumMulitpleChoiceField,
    validate_gpgkey,
    validate_signature, NativeSplitDateTimeWidget, NativeDateInput,
)
from inyoka.utils.sessions import SurgeProtectionMixin
from inyoka.utils.text import slugify
from inyoka.utils.urls import href
from inyoka.utils.user import is_valid_username

UserModel = get_user_model()

#: Some constants used for ChoiceFields
GLOBAL_PRIVILEGE_MODELS = {
    'forum': ('forum', 'topic'),
    'ikhaya': ('article', 'category', 'comment', 'report', 'suggestion',),
    'auth': ('group',),
    'pastebin': ('entry',),
    'planet': ('entry', 'blog',),
    'portal': ('event', 'user', 'staticfile', 'staticpage', 'storage', 'linkmap'),
}

NOTIFY_BY_CHOICES = (
    ('mail', gettext_lazy('Mail')),
)

NOTIFICATION_CHOICES = (
    ('topic_move', gettext_lazy('A subscribed topic was moved')),
    ('topic_split', gettext_lazy('A subscribed topic was split')),
    ('pm_new', gettext_lazy('I received a message'))
)


LinkMapFormset = modelformset_factory(Linkmap, fields=('token', 'url', 'icon'), extra=3, can_delete=True)


class LoginForm(AuthenticationForm):
    """Simple form for the login dialog"""
    permanent = forms.BooleanField(label=gettext_lazy('Keep logged in'), required=False,
                                   help_text=_("Don’t choose this option if you are using a public computer."
                                               " Otherwise, unauthorized persons may enter your account."))

    mail = settings.INYOKA_CONTACT_EMAIL

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        self.fields['username'].label = _('Username or email address')

        # adapt max length for emails (super class only considered username max_length)
        username_max_length = max(User.username.field.max_length, User.email.field.max_length)
        self.fields["username"].validators.append(validators.MaxLengthValidator(username_max_length))
        self.fields["username"].max_length = username_max_length
        self.fields["username"].widget.attrs["maxlength"] = username_max_length

        self.error_messages['inactive'] = format_html(
                _("Login failed because the user is inactive. You probably didn’t click on the link in the "
                  "activation mail which was sent to you after your registration. If it is still not working, contact "
                  "us: <a href=\"{mailto}\">{mail}</a>"),
                mail=self.mail, mailto=f"mailto:{self.mail}",
                )

    def clean(self):
        try:
            super().clean()
        except UserBanned:
            raise ValidationError(format_html(
                _("Login failed because the user is currently banned. You were informed about that. If you "
                  "don’t agree with the ban or if it is a mistake, please contact <a href=\"{mailto}\">{mail}</a>."
                  ),
                mail=self.mail, mailto=f"mailto:{self.mail}",
                ),
                code="banned",
            )

        return self.cleaned_data


class RegisterForm(forms.Form):
    """
    Form for registering a new user account.

    Validates that the requested username is not already in use, and
    requires the password to be entered twice to catch typos.
    The user also needs to confirm our terms of usage and there are some
    techniques for bot catching included e.g a CAPTCHA and a hidden captcha
    for bots that just fill out everything.
    """
    username = forms.CharField(label=gettext_lazy('Username'), max_length=20)
    email = EmailField(label=gettext_lazy('E-mail'),
        help_text=gettext_lazy('We need your email '
        'address to send you a new password if you forgot it. It is not '
        'visible to other users. For more information, check out our '
        '<a href="%(link)s">privacy policy</a>.') % {
            'link': href('portal', 'datenschutz')})
    password = forms.CharField(label=gettext_lazy('Password'),
        widget=forms.PasswordInput(render_value=False))
    confirm_password = forms.CharField(label=gettext_lazy('Confirm password'),
        widget=forms.PasswordInput(render_value=False))
    captcha = CaptchaField(label=gettext_lazy('CAPTCHA'))
    terms_of_usage = forms.BooleanField()

    use_required_attribute = False

    def clean_username(self):
        """
        Validates that the username is alphanumeric and is not already
        in use.
        """
        username = self.cleaned_data['username']

        if not is_valid_username(username):
            raise forms.ValidationError(
                _('Your username contains invalid characters. Only '
                  'alphanumeric chars and “-” are allowed.')
            )

        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError(
                _('This username is not available, please try another one.')
            )

        # prevent email address as username
        try:
            validate_email(username)
        except ValidationError:
            return username
        else:
            raise forms.ValidationError(
                _('Please do not enter an email address as username.')
            )

    def clean(self):
        """
        Validates that the two password inputs match.
        """
        if 'password' in self.cleaned_data and 'confirm_password' in self.cleaned_data:
            if self.cleaned_data['password'] == self.cleaned_data['confirm_password']:
                return self.cleaned_data
            raise forms.ValidationError(
                _('The password must match the password confirmation.')
            )
        else:
            raise forms.ValidationError(
                _('You need to enter a password and a password confirmation.')
            )

    def clean_terms_of_usage(self):
        """Validates that the user agrees our terms of usage"""
        if self.cleaned_data.get('terms_of_usage', False):
            return True
        raise forms.ValidationError(
            _('You need to read and accept our terms and conditions.')
        )

    def clean_email(self):
        """
        Validates if the required field `email` contains
        a non-existing mail address.
        """
        exists = User.objects.filter(email__iexact=self.cleaned_data['email'])\
                             .exists()
        if exists:
            raise forms.ValidationError(format_html(
                _('The given email address is already in use. If you forgot '
                  'your password, you can <a href="{link}">restore it</a>.'),
                link=href('portal', 'lost_password')))
        return self.cleaned_data['email']


class LostPasswordForm(auth_forms.PasswordResetForm):

    def get_users(self, email):
        """
        Customized from upstream Django. Django believes `is_active` to be a field
        in the database, but it is not in our data model.
        """
        from django.contrib.auth.forms import _unicode_ci_compare

        email_field_name = UserModel.get_email_field_name()
        possible_users = UserModel._default_manager.filter(**{
            '%s__iexact' % email_field_name: email,
        })

        return (
            u for u in possible_users
            if u.has_usable_password() and
               u.is_active and
            _unicode_ci_compare(email, getattr(u, email_field_name))
        )


class UserCPSettingsForm(forms.Form):
    """
    Form used for the user control panel – dialog.
    """
    notify = forms.MultipleChoiceField(
        label=gettext_lazy('Notify via'), required=False,
        choices=NOTIFY_BY_CHOICES,
        widget=forms.CheckboxSelectMultiple)
    notifications = forms.MultipleChoiceField(
        label=gettext_lazy('Notify me if'), required=False,
        choices=NOTIFICATION_CHOICES,
        widget=forms.CheckboxSelectMultiple)
    ubuntu_version = forms.MultipleChoiceField(
        label=gettext_lazy('Notifications on topics with a specific Ubuntu version'),
        required=False, widget=forms.CheckboxSelectMultiple)
    timezone = forms.ChoiceField(label=gettext_lazy('Timezone'), required=True,
        choices=list(zip(TIMEZONES, TIMEZONES)))
    hide_profile = forms.BooleanField(label=gettext_lazy('Hide online status'),
                                      required=False)
    hide_avatars = forms.BooleanField(label=gettext_lazy('Hide avatars'),
                                      required=False)
    hide_signatures = forms.BooleanField(label=gettext_lazy('Hide signatures'),
                                         required=False)
    autosubscribe = forms.BooleanField(required=False,
                        label=gettext_lazy('Subscribe to a topic when replying'))
    show_preview = forms.BooleanField(required=False,
        label=gettext_lazy('Attachment preview'))
    show_thumbnails = forms.BooleanField(required=False,
        label=gettext_lazy('Picture preview'),
        help_text=gettext_lazy('No effect if “attachment preview” is disabled'))
    highlight_search = forms.BooleanField(required=False,
        label=gettext_lazy('Highlight search'))
    mark_read_on_logout = forms.BooleanField(required=False,
        label=gettext_lazy('Mark all forums as “read” on logout'))
    reduce_motion = forms.BooleanField(required=False, label=gettext_lazy('Reduced motion'),
                                        help_text=gettext_lazy('If enabled, less animations are used.'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['ubuntu_version'].choices = get_simple_version_choices()


class UserCPProfileForm(forms.ModelForm):
    use_gravatar = forms.BooleanField(label=gettext_lazy('Use Gravatar'), required=False)
    email = EmailField(label=gettext_lazy('Email'), required=True)

    show_email = forms.BooleanField(required=False)

    coordinates = forms.CharField(label=gettext_lazy('Coordinates (latitude, longitude)'),
                                  required=False)
    gpgkey = forms.CharField(validators=[validate_gpgkey], min_length=40, max_length=255,
                             label=gettext_lazy('GPG fingerprint'), required=False)

    userpage = forms.CharField(widget=forms.Textarea, required=False)

    class Meta:
        model = User
        fields = ['jabber', 'signature', 'location', 'website', 'gpgkey',
                  'launchpad', 'avatar']

    def __init__(self, *args, **kwargs):
        instance = kwargs['instance']
        self.admin_mode = kwargs.pop('admin_mode', False)

        # kwargs['initial'] can already exist from subclass EditUserProfileForm
        initial = kwargs['initial'] = kwargs.get('initial', {})

        initial.update({
            k: v for k, v in instance.settings.items()
             if k.startswith('show_')
        })
        initial['use_gravatar'] = instance.settings.get('use_gravatar', False)
        initial['email'] = instance.email

        if hasattr(instance, 'userpage'):
            initial['userpage'] = instance.userpage.content

        self.old_email = instance.email
        self.old_avatar = instance.avatar.name if instance.avatar else None
        self.change_avatar = False
        super().__init__(*args, **kwargs)

    def clean_gpgkey(self):
        gpgkey = self.cleaned_data.get('gpgkey', '').upper()
        if gpgkey.startswith('0X'):
            gpgkey = gpgkey[2:]
        gpgkey = gpgkey.replace(' ', '')
        return gpgkey

    def clean_signature(self):
        signature = self.cleaned_data.get('signature', '')
        validate_signature(signature)
        return signature

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(
                _('This email address is already in use.'))
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
        with Image.open(avatar) as image:
            format = image.format
            max_size = (settings.INYOKA_AVATAR_MAXIMUM_WIDTH,
                        settings.INYOKA_AVATAR_MAXIMUM_HEIGHT)
            if any(length > max_length for max_length, length in zip(max_size, image.size)):
                image = image.resize(max_size)
            out = io.BytesIO()
            image.save(out, format)
        self.change_avatar = True
        return ContentFile(out.getvalue(), 'avatar.' + format.lower())

    def save(self, request, commit=True):
        data = self.cleaned_data
        user = super().save(commit=False)

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
                    _('You’ve been sent an email to confirm your new email '
                      'address.'))

        for key in ('show_email', 'use_gravatar'):
            user.settings[key] = data[key]

        if data['userpage']:
            if hasattr(user, 'userpage'):
                userpage = user.userpage
            else:
                userpage = UserPage(user=user)
            userpage.content = data['userpage']
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
        fields = UserCPProfileForm.Meta.fields + ['icon', 'username', 'member_title']

    def __init__(self, *args, **kwargs):
        instance = kwargs['instance']

        initial = kwargs['initial'] = {}
        if instance.icon:
            initial['icon'] = os.path.join(settings.MEDIA_ROOT, instance.icon)

        super().__init__(*args, **kwargs)

    def clean_username(self):
        """
        Validates that the username is alphanumeric and is not already
        in use.
        """
        data = self.cleaned_data
        username = data['username']
        if not is_valid_username(username):
            raise forms.ValidationError(
                _('Your username contains invalid characters. Only '
                  'alphanumeric chars and “-” are allowed.')
            )
        exists = User.objects.filter(username=username).exists()
        if self.instance.username != username and exists:
            raise forms.ValidationError(
                _('A user with this name already exists.'))
        return username

    def clean_icon(self):
        icon = self.cleaned_data.get('icon')
        if icon:
            return os.path.relpath(icon, settings.MEDIA_ROOT)
        else:
            return icon


class EditUserGroupsForm(forms.Form):
    groupWidget = forms.CheckboxSelectMultiple(
        attrs={'id': 'portal-user-groupselector',
               'class': 'portal-user-groupselector'}
    )
    groups = forms.ModelMultipleChoiceField(
        label=gettext_lazy('Please select the groups for this user.'),
        required=False, queryset=Group.objects.all().order_by('name'), widget=groupWidget)

    def clean_groups(self):
        if self.cleaned_data['groups']:
            self.all_groups = set(Group.objects.all())
            self.selected_groups = set(self.cleaned_data['groups'])
            if self.selected_groups.issubset(self.all_groups):
                return self.cleaned_data['groups']
            else:
                raise forms.ValidationError(_('Invalid groups specified.'))
        return self.cleaned_data['groups']

    def save(self, commit=True):
        if commit:
            active_groups = set(self.user.groups.all())
            remove_groups = active_groups - self.selected_groups
            assign_groups = self.selected_groups - active_groups
            for group in remove_groups:
                self.user.groups.remove(group)
            for group in assign_groups:
                self.user.groups.add(group)
            cache.delete('/acl/%s' % self.user.id)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('instance', None)
        super().__init__(*args, **kwargs)


class CreateUserForm(forms.Form):
    username = forms.CharField(label=gettext_lazy('Username'), max_length=30)
    password = forms.CharField(label=gettext_lazy('Password'),
        widget=forms.PasswordInput(render_value=False))
    confirm_password = forms.CharField(label=gettext_lazy('Confirm password'),
        widget=forms.PasswordInput(render_value=False))
    email = EmailField(label=gettext_lazy('Email'))
    authenticate = forms.BooleanField(label=gettext_lazy('Authenticate'), initial=True,
        required=False, help_text=(gettext_lazy('The user will be send a confirmation '
            'mail and set to “inactive”.')))

    def clean_username(self):
        """
        Validates that the username is alphanumeric and is not already
        in use.
        """
        data = self.cleaned_data
        username = data['username']
        if not is_valid_username(username):
            raise forms.ValidationError(
                _('Your username contains invalid characters. Only '
                  'alphanumeric chars and “-” are allowed.')
            )
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError(
                _('The username is already in use. Please choose another one.'))
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
                _('The password must match the password confirmation.')
            )
        else:
            raise forms.ValidationError(
                _('You need to enter a password and a password confirmation.')
            )

    def clean_email(self):
        """
        Validates if the required field `email` contains
        a non existing mail address.
        """
        if 'email' in self.cleaned_data:
            if User.objects.filter(email__iexact=self.cleaned_data['email']).exists():
                raise forms.ValidationError(_('This email address is already in use.'))
            return self.cleaned_data['email']
        else:
            raise forms.ValidationError(_('You need to enter a email address'))


class EditUserStatusForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['banned_until'].localize = True

    class Meta:
        model = User
        fields = ['status', 'banned_until']
        field_classes = {
            'banned_until': SplitDateTimeField,
        }
        widgets = {
            'banned_until': NativeSplitDateTimeWidget(),
        }

    def clean(self):
        """Keep the user from setting banned_until if status is not banned.
        """
        data = self.cleaned_data

        if not data.get('banned_until'):
            return data

        if int(data['status']) != User.STATUS_BANNED:
            raise forms.ValidationError(_('The user is not banned'))
        if data['banned_until'] < dj_timezone.now():
            raise forms.ValidationError(_('The point of time is in the past.'))

        return data


class EditUserPasswordForm(forms.Form):
    new_password = forms.CharField(label=gettext_lazy('New password'),
        required=False, widget=forms.PasswordInput(render_value=False))
    confirm_password = forms.CharField(label=gettext_lazy('Confirm new password'),
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
                _('The password must match the password confirmation.')
            )
        else:
            raise forms.ValidationError(
                _('You need to enter a password and a password confirmation.')
            )


class UserMailForm(forms.Form):
    text = forms.CharField(
        label=gettext_lazy('Text'),
        widget=forms.Textarea(),
        help_text=gettext_lazy(
            'The message will be send as “plain text”. Your username '
            'will be noted as sender.'),
    )


class EditGroupForm(forms.ModelForm):
    name = forms.CharField(label=gettext_lazy('Groupname'), required=True)

    class Meta:
        model = Group
        fields = ('name',)

    def clean_name(self):
        """Validates that the name is alphanumeric"""
        data = self.cleaned_data
        groupname = data['name']
        if not is_valid_username(groupname):
            raise forms.ValidationError(_(
                'The group name contains invalid chars'))
        if Group.objects.filter(name__iexact=groupname).exists():
            raise forms.ValidationError(
                _('The groupname is already in use. Please choose another one.'))
        return groupname


def get_permissions_for_app(application, filtered=None):
    """
    Select all permissions for the models defined in
    ``GLOBAL_PRIVILEGE_MODELS`` for ``application`` and return a "list" of
    two-tuples of the form
    ``('app_label.permission_codename', 'Permission Name')``
    orderd by the ``'app_label.permission_codename'``.

    An optional ``filtered`` argument helps to filter out unwanted/unused
    permissions.
    """
    permissions = Permission.objects.filter(
        content_type__app_label=application,
        content_type__model__in=GLOBAL_PRIVILEGE_MODELS[application]
    ).select_related('content_type').annotate(
        code=Concat(
            'content_type__app_label', Value('.'), 'codename',
            output_field=CharField()
        )
    ).order_by('code').values_list('code', 'name')
    if filtered:
        return [
            perm
            for perm in permissions
            if perm[0] not in filtered
        ]
    return permissions


def make_permission_choices(application, filtered=None):
    """
    Wrapper around :func:`.get_permissions_for_app` returning a callable.
    Useful for e.g. form field choices.
    """
    return functools.partial(get_permissions_for_app, application, filtered)

def permission_choices_to_permission_strings(application):
    return {perm[0] for perm in get_permissions_for_app(application)}


def permission_to_string(permission):
    permission_code, app_label = permission.natural_key()[0:2]
    return '%s.%s' % (app_label, permission_code)


class GroupGlobalPermissionForm(forms.Form):
    MANAGED_APPS = ('auth', 'ikhaya', 'portal', 'pastebin', 'planet', 'forum')
    AUTH_FILTERED_PERMISSIONS = (
        'auth.delete_group',
        'auth.view_group',
        'auth.add_permission',
        'auth.change_permission',
        'auth.delete_permission',
    )
    IKHAYA_FILTERED_PERMISSIONS = (
        'ikhaya.add_article',
        'ikhaya.view_article',
        'ikhaya.add_category',
        'ikhaya.view_category',
        'ikhaya.add_comment',
        'ikhaya.view_comment',
        'ikhaya.add_report',
        'ikhaya.view_report',
        'ikhaya.add_suggestion',
        'ikhaya.view_suggestion',
        'ikhaya.change_report',
        'ikhaya.change_suggestion',
        'ikhaya.delete_category',
        'ikhaya.delete_comment',
        'ikhaya.delete_report',
    )
    PORTAL_FILTERED_PERMISSIONS = (
        'portal.view_event',
        'portal.delete_user',
        'portal.view_user',
        'portal.add_staticfile',
        'portal.view_staticfile',
        'portal.add_staticpage',
        'portal.view_staticpage',
        'portal.add_storage',
        'portal.delete_storage',
        'portal.view_storage',
        'portal.add_linkmap',
        'portal.delete_linkmap',
        'portal.view_linkmap',
    )
    FORUM_FILTERED_PERMISSIONS = (
        'forum.add_forum',
        'forum.add_reply_forum',
        'forum.add_topic',
        'forum.add_topic_forum',
        'forum.change_topic',
        'forum.delete_forum',
        'forum.delete_topic',
        'forum.delete_topic_forum',
        'forum.moderate_forum',
        'forum.poll_forum',
        'forum.sticky_forum',
        'forum.upload_forum',
        'forum.view_forum',
        'forum.view_topic',
        'forum.vote_forum',
    )
    PASTEBIN_FILTERED_PERMISSIONS = (
        'pastebin.change_entry',
    )
    PLANET_FILTERED_PERMISSIONS = (
        'planet.add_blog',
        'planet.add_entry',
        'planet.view_entry',
        'planet.change_entry',
        'planet.delete_entry',
        'planet.delete_blog',
    )
    auth_permissions = forms.MultipleChoiceField(
        choices=make_permission_choices('auth', AUTH_FILTERED_PERMISSIONS),
        widget=forms.CheckboxSelectMultiple,
        label=gettext_lazy('Auth'),
        required=False)
    ikhaya_permissions = forms.MultipleChoiceField(
        choices=make_permission_choices('ikhaya', IKHAYA_FILTERED_PERMISSIONS),
        widget=forms.CheckboxSelectMultiple,
        label=gettext_lazy('Ikhaya'),
        required=False)
    portal_permissions = forms.MultipleChoiceField(
        choices=make_permission_choices('portal', PORTAL_FILTERED_PERMISSIONS),
        widget=forms.CheckboxSelectMultiple,
        label=gettext_lazy('Portal'),
        required=False)
    pastebin_permissions = forms.MultipleChoiceField(
        choices=make_permission_choices('pastebin', PASTEBIN_FILTERED_PERMISSIONS),
        widget=forms.CheckboxSelectMultiple,
        label=gettext_lazy('Pastebin'),
        required=False)
    planet_permissions = forms.MultipleChoiceField(
        choices=make_permission_choices('planet', PLANET_FILTERED_PERMISSIONS),
        widget=forms.CheckboxSelectMultiple,
        label=gettext_lazy('Planet'),
        required=False)
    forum_permissions = forms.MultipleChoiceField(
        choices=make_permission_choices('forum', FORUM_FILTERED_PERMISSIONS),
        widget=forms.CheckboxSelectMultiple,
        label=gettext_lazy('Forum'),
        required=False)

    def _clean_permissions(self, modulename):
        module_permissions = permission_choices_to_permission_strings(modulename)
        if self.cleaned_data['%s_permissions' % modulename]:
            active_permissions = set(self.cleaned_data['%s_permissions' % modulename])
            if active_permissions.issubset(module_permissions):
                return active_permissions
            else:
                raise forms.ValidationError('Invalid Permissions specified.')

    def _sync_permissions(self, modulename):
        active_permissions = set()
        if self.cleaned_data['%s_permissions' % modulename]:
            active_permissions = set(self.cleaned_data['%s_permissions' % modulename])
        current_permissions = {
            perm
            for perm in self.instance_permissions
            if perm.startswith(modulename)
        }
        remove_permissions = current_permissions - active_permissions
        assign_permissions = active_permissions - current_permissions
        for perm in remove_permissions:
            remove_perm(perm, self.instance)
        for perm in assign_permissions:
            assign_perm(perm, self.instance)

    def clean_auth_permissions(self):
        return self._clean_permissions('auth')

    def clean_ikhaya_permissions(self):
        return self._clean_permissions('ikhaya')

    def clean_portal_permissions(self):
        return self._clean_permissions('portal')

    def clean_pastebin_permissions(self):
        return self._clean_permissions('pastebin')

    def clean_planet_permissions(self):
        return self._clean_permissions('planet')

    def clean_forum_permissions(self):
        return self._clean_permissions('forum')

    def save(self, commit=True):
        if self.instance and commit:
            for app in self.MANAGED_APPS:
                self._sync_permissions(app)
            cache.delete_pattern('/acl/*')

    def __init__(self, *args, **kwargs):
        initial = {}
        self.instance = None
        if 'instance' in kwargs:
            self.instance = kwargs.pop('instance')
            self.instance_permissions = [
                permission_to_string(perm)
                for perm in self.instance.permissions.all()
            ]
            for field in self.MANAGED_APPS:
                field_permissions = [
                    perm
                    for perm in self.instance_permissions
                    if perm.startswith(field)
                ]
                initial['%s_permissions' % field] = field_permissions
        super().__init__(initial=initial, *args, **kwargs)


class GroupForumPermissionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('instance', None)
        super().__init__(*args, **kwargs)
        if self.instance:
            self.instance_permissions = [
                permission_to_string(perm)
                for perm in self.instance.permissions.all()
            ]
        FORUM_FILTERED_PERMISSIONS = (
            'forum.add_forum',
            'forum.add_topic',
            'forum.change_topic',
            'forum.change_forum',
            'forum.delete_forum',
            'forum.delete_topic',
            'forum.manage_reported_topic',
            'forum.view_topic',
        )
        forums = [tuple[1] for tuple in Forum.get_children_recursive(Forum.objects.get_sorted())]
        for forum in forums:
            field = ForumMulitpleChoiceField(
                choices=make_permission_choices('forum', FORUM_FILTERED_PERMISSIONS),
                widget=forms.CheckboxSelectMultiple,
                label=forum.name,
                is_category=forum.is_category,
                required=False,
            )
            if self.instance:
                field.initial = self._forum_instance_permissions(forum)
            self.fields['forum_%s_permissions' % forum.id] = field

    @property
    def _forum_fields(self):
        return [
            (fieldname, self.cleaned_data[fieldname])
            for fieldname in self.cleaned_data
            if fieldname.startswith('forum_')
        ]

    def _forum_instance_permissions(self, forum):
        return [
            'forum.%s' % perm
            for perm in get_perms(self.instance, forum)
        ]

    def clean(self):
        super().clean()
        module_permissions = permission_choices_to_permission_strings('forum')
        for fieldname, values in self._forum_fields:
            if values:
                values = set(values)
                if not values.issubset(module_permissions):
                    raise forms.ValidationError(_('Invalid Permissions specified.'))

    def save(self, commit=True):
        for forum in Forum.objects.all():
            forum_key = 'forum_%s_permissions' % forum.id
            if self.cleaned_data[forum_key]:
                active_permissions = set(self._forum_instance_permissions(forum))
                wanted_permissions = set(self.cleaned_data[forum_key])
                delete_permissions = active_permissions - wanted_permissions
                assign_permissions = wanted_permissions - active_permissions
                for perm in assign_permissions:
                    assign_perm(perm, self.instance, forum)
            else:
                delete_permissions = self._forum_instance_permissions(forum)
            for perm in delete_permissions:
                remove_perm(perm, self.instance, forum)
        cache.delete_pattern('/acl/*')


class PrivateMessageForm(forms.Form):
    """Form for writing a new private message"""
    recipient = forms.CharField(label=gettext_lazy('To'), required=False,
        help_text=gettext_lazy('Separate multiple names by semicolon'))
    group_recipient = forms.CharField(label=gettext_lazy('Groups'), required=False,
        help_text=gettext_lazy('Separate multiple groups by semicolon'))
    subject = forms.CharField(label=gettext_lazy('Subject'),
                              widget=forms.TextInput(attrs={'size': 50}))
    text = forms.CharField(label=gettext_lazy('Message'), widget=forms.Textarea)

    def clean(self):
        d = self.cleaned_data
        if 'recipient' in d and 'group_recipient' in d:
            if not d['recipient'].strip() and not d['group_recipient'].strip():
                raise forms.ValidationError(_('Please enter at least one receiver.'))
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
                label=gettext_lazy('Number of entries in the feed'),
                help_text=gettext_lazy('The number will be round off to keep the server '
                            'load low.'))
    mode = forms.ChoiceField(initial='short',
        choices=(('full', gettext_lazy('Full article')),
                 ('short', gettext_lazy('Only introduction')),
                 ('title', gettext_lazy('Only title'))),
        widget=forms.RadioSelect(attrs={'class': 'radioul'}))

    def clean(self):
        data = self.cleaned_data
        data['count'] = _feed_count_cleanup(data.get('count', 20))
        return data


class ForumFeedSelectorForm(FeedSelectorForm):
    component = forms.ChoiceField(initial='forum',
        choices=(('*', ''), ('forum', ''), ('topic', '')))
    forum = forms.ChoiceField(required=False)

    def clean_forum(self):
        data = self.cleaned_data
        if data.get('component') == 'forum' and not data.get('forum'):
            raise forms.ValidationError(_('Please select a forum'))
        return data['forum']


class IkhayaFeedSelectorForm(FeedSelectorForm):
    category = forms.ChoiceField(label=gettext_lazy('Category'))


class PlanetFeedSelectorForm(FeedSelectorForm):
    pass


class WikiFeedSelectorForm(FeedSelectorForm):
    #: `mode` is never used but needs to be overwritten because of that.
    mode = forms.ChoiceField(required=False)
    page = forms.CharField(label=_('Page name'), required=False,
                           help_text=(gettext_lazy('If not given, the last changes will '
                                        'be displayed.')))


class EditStaticPageForm(forms.ModelForm):

    class Meta:
        model = StaticPage
        fields = ('key', 'title', 'content')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.new = self.instance.key == ""

        self.fields['key'].required = not self.new
        self.fields['key'].widget.attrs['readonly'] = not self.new

    def clean_key(self):
        key = self.cleaned_data['key']

        if not self.new and self.instance.key != key:
            raise forms.ValidationError(_('It is not allowed to change this key.'))

        return key

    def clean(self):
        super().clean()

        key = self.cleaned_data.get('key')
        title = self.cleaned_data.get('title')

        if title and self.new:  # at least the title is needed to create a key
            if not key:
                key = slugify(title)

            if StaticPage.objects.filter(key__iexact=key).exists():
                raise forms.ValidationError(
                    _('Another page with this name already exists. Please '
                      'edit this page.')
                )

            self.cleaned_data['key'] = key


class EditFileForm(forms.ModelForm):
    class Meta:
        model = StaticFile
        exclude = ['identifier']

    def clean_file(self):
        data = self.cleaned_data
        if 'file' in data and StaticFile.objects.filter(
                identifier__iexact=str(data['file'])).exists():
            raise forms.ValidationError(_('Another file with this name '
                'already exists. Please edit this file.'))
        return data['file']

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.identifier = instance.file.name.rsplit('/', 1)[-1]
        if commit:
            instance.save()
        return instance


class ConfigurationForm(forms.Form):
    global_message = forms.CharField(label=gettext_lazy('Global Message'),
        widget=forms.Textarea(attrs={'rows': 3}), required=False,
        help_text=gettext_lazy('This message will displayed on every page in the '
                      'header. To disable it, leave the field empty.'))
    welcome_message = forms.CharField(label=gettext_lazy('Welcome Message'),
        widget=forms.Textarea(attrs={'rows': 5}), required=False,
        help_text=gettext_lazy('This is the welcome message displayed on the main page.'))
    blocked_hosts = forms.CharField(label=gettext_lazy('Blocked hosts for email addresses'),
        widget=forms.Textarea(attrs={'rows': 5}), required=False,
        help_text=gettext_lazy('Users cannot use email addresses from these hosts to '
                      'register an account.'))
    team_icon = forms.ImageField(label=gettext_lazy('Global team icon'), required=False,
        help_text=gettext_lazy('Please note the details on the maximum size below.'))
    wiki_newpage_template = forms.CharField(required=False,
        widget=forms.Textarea(attrs={'rows': 5}),
        label=gettext_lazy('Default text of new wiki pages'))
    wiki_newpage_root = forms.CharField(required=False,
        label=gettext_lazy('Location of new wiki pages'))
    wiki_newpage_infopage = forms.CharField(required=False,
        label=gettext_lazy('Information page about new wiki pages'),
        help_text=gettext_lazy('Information page to which a “create” link should '
                    'redirect to.'))
    wiki_edit_note = forms.CharField(required=False,
        widget=forms.Textarea(attrs={'rows': 5}),
        label=gettext_lazy('Wiki helptext'),
        help_text=gettext_lazy('This text appears above the wiki editor.'))
    license_note = forms.CharField(required=False, label=gettext_lazy('License note'),
                                   widget=forms.Textarea(attrs={'rows': 2}))
    countdown_active = forms.BooleanField(required=False,
        label=gettext_lazy('Display countdown'))
    countdown_target_page = forms.CharField(required=False,
        label=gettext_lazy('Full path to the target link page'))
    countdown_image_url = forms.CharField(required=False,
        label=gettext_lazy('Image URL'),
        help_text=gettext_lazy('The complete URL to the countdown banner. '
                    'Use <code>%(remaining)s</code> to be replaced by the '
                    'remaining days or <code>soon</code>.'))
    countdown_date = forms.DateField(label=gettext_lazy('Release date'),
        required=False, widget=NativeDateInput, localize=True)
    distri_versions = forms.CharField(required=False, widget=HiddenInput())

    ikhaya_description = forms.CharField(required=False,
        widget=forms.Textarea(attrs={'rows': 5}),
        label=gettext_lazy('Description about Ikhaya that will be used '
                            'on the start page and in the feed aggregations.'))
    planet_description = forms.CharField(required=False,
        widget=forms.Textarea(attrs={'rows': 5}),
        label=gettext_lazy('Description about the planet that will be used '
                            'on the planet page and in the feed aggregations.'))

    def clean_distri_versions(self):
        data = self.cleaned_data
        key = 'distri_versions'
        try:
            data[key] = data.get(key, '[]')
            # is there a way to validate a JSON string?
            json.loads(data[key])
        except ValueError:
            return '[]'
        return data[key]

    def clean_countdown_image_url(self):
        data = self.cleaned_data.get('countdown_image_url', '')
        try:
            data % {'remaining': 'soon'}
        except KeyError:
            raise forms.ValidationError(_('Invalid substitution pattern.'))
        return data


class TokenForm(forms.Form):
    token = forms.CharField(
        label=gettext_lazy('Please enter the string which was sent to you by email'),
        widget=forms.Textarea())

    def __init__(self, *args, **kwargs):
        if 'action' in kwargs:
            self.action = kwargs.pop('action')
        super().__init__(*args, **kwargs)

    def clean_token(self):
        def get_action_and_limit():
            if self.action == 'reactivate_user':
                return reactivate_user, settings.USER_REACTIVATION_LIMIT
            elif self.action == 'set_new_email':
                return set_new_email, settings.USER_SET_NEW_EMAIL_LIMIT
            elif self.action == 'reset_email':
                return reset_email, settings.USER_RESET_EMAIL_LIMIT

        salt = 'inyoka.action.%s' % self.action
        token = self.cleaned_data['token']
        func, lifetime = get_action_and_limit()
        try:
            token = signing.loads(token,
                                  max_age=lifetime * 24 * 60 * 60,
                                  salt=salt)
        except (ValueError, signing.BadSignature):
            raise forms.ValidationError(_('The entered token is invalid or has expired.'))
        return func(**token)
