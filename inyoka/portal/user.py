"""
    inyoka.portal.user
    ~~~~~~~~~~~~~~~~~~

    Our own user model used for implementing our own
    permission system and our own administration center.

    :copyright: (c) 2007-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import os
import secrets
import string
from datetime import datetime
from json import dumps, loads

from django.conf import settings
from django.conf import settings as inyoka_settings
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    Group,
    PermissionsMixin,
    update_last_login,
)
from django.contrib.auth.signals import user_logged_in
from django.core import signing
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models.functions import Upper
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.utils.html import escape
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from guardian.mixins import GuardianUserMixin
from guardian.shortcuts import get_perms

from inyoka.utils.cache import QueryCounter
from inyoka.utils.database import InyokaMarkupField, JabberField, JSONField
from inyoka.utils.decorators import deferred
from inyoka.utils.gravatar import get_gravatar
from inyoka.utils.mail import send_mail
from inyoka.utils.urls import href
from inyoka.utils.user import gen_activation_key, is_valid_username


class UserBanned(Exception):
    """
    Simple exception that is raised while
    log-in to give the user a somewhat detailed
    exception.
    """


def reactivate_user(id, email, status):

    email_exists = User.objects.filter(email=email).exists()
    if email_exists:
        msg = _('This e-mail address is used by another user.')
        raise ValidationError(msg)

    user = User.objects.get(id=id)
    if not user.is_deleted:
        raise ValidationError(_('The account “%(name)s” was already reactivated.') %
                              {'name': escape(user.username)},)

    user.email = email
    user.status = status

    if user.banned_until and user.banned_until < datetime.utcnow():
        # User was banned but the ban time exceeded
        user.status = User.STATUS_ACTIVE
        user.banned_until = None

    # Set a dummy password
    user.set_random_password()
    user.save()

    # Enforce registered group if active.
    if user.status == User.STATUS_ACTIVE:
        user.groups.add(Group.objects.get(name=settings.INYOKA_REGISTERED_GROUP_NAME))

    return _('The account “%(name)s” was reactivated. Please use the '
             'password recovery function to set a new password.') % {'name': escape(user.username)}


def deactivate_user(user):
    """
    This deactivates a user and removes all personal information.
    To avoid abuse, an email is sent that allows reactivation of the account
    within the next month.
    """

    data = {
        'id': user.id,
        'email': user.email,
        'status': user.status,
    }

    subject = _('Deactivation of your account “%(name)s” on %(sitename)s') % {
        'name': escape(user.username),
        'sitename': settings.BASE_DOMAIN_NAME}
    text = render_to_string('mails/account_deactivate.txt', {
        'user': user,
        'token': signing.dumps(data, salt='inyoka.action.reactivate_user'),
    })
    user.email_user(subject, text, settings.INYOKA_SYSTEM_USER_EMAIL)

    user.status = User.STATUS_DELETED
    user.email = 'user%d@ubuntuusers.de.invalid' % user.id
    user.set_unusable_password()
    user.groups.clear()
    user.avatar = None
    user.jabber = user.location = user.signature = user.gpgkey = \
        user.location = user.website = user.launchpad = user.member_title = ''
    user.save()


def send_new_email_confirmation(user, email):
    """Send the user an email where he can confirm his new email address"""
    data = {
        'id': user.id,
        'email': email,
    }

    text = render_to_string('mails/new_email_confirmation.txt', {
        'user': user,
        'token': signing.dumps(data, salt='inyoka.action.set_new_email'),
    })
    subject = _('%(sitename)s – Confirm email address') % {
        'sitename': settings.BASE_DOMAIN_NAME
    }
    send_mail(subject, text, settings.INYOKA_SYSTEM_USER_EMAIL, [email])


def set_new_email(id, email):
    """
    Save the new email address the user has confirmed, and send an email to
    his old address where he can reset it to protect against abuse.
    """
    user = User.objects.get(id=id)

    data = {
        'id': user.id,
        'email': user.email,
    }
    text = render_to_string('mails/reset_email.txt', {
        'user': user,
        'new_email': email,
        'token': signing.dumps(data, salt='inyoka.action.reset_email'),
    })
    subject = _('%(sitename)s – Email address changed') % {
        'sitename': settings.BASE_DOMAIN_NAME
    }
    user.email_user(subject, text, settings.INYOKA_SYSTEM_USER_EMAIL)

    user.email = email
    user.save()
    return _('Your new email address was saved.')


def reset_email(id, email):
    user = User.objects.get(id=id)
    user.email = email
    user.save()

    return _('Your email address was reset.')


def send_activation_mail(user):
    """send an activation mail"""
    message = render_to_string('mails/activation_mail.txt', {
        'user': user,
        'email': user.email,
        'activation_key': gen_activation_key(user)
    })
    subject = _('%(sitename)s – Activation of the user “%(name)s”') % {
        'sitename': settings.BASE_DOMAIN_NAME,
        'name': user.username}
    send_mail(subject, message, settings.INYOKA_SYSTEM_USER_EMAIL, [user.email])


class UserManager(BaseUserManager):
    def get_by_username_or_email(self, name):
        """Get a user by its username or email address"""
        try:
            user = User.objects.get(username__iexact=name)
        except User.DoesNotExist as exc:
            # fallback to email
            if '@' in name:
                user = User.objects.get(email__iexact=name)
            else:
                raise exc
        return user

    def create_user(self, username, email, password=None):
        now = datetime.utcnow()
        user = self.model(username=username, email=email.strip().lower(),
                          status=User.STATUS_INACTIVE, date_joined=now, last_login=now)

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save()
        return user

    def register_user(self, username, email, password, send_mail=True):
        """
        Create a new inactive user and send him an
        activation e-mail.

        :Parameters:
            username
                The username for the new user.
            email
                The user's email.
                (It's also where the activation mail will be sent to.)
            password
                The user's password.
            send_mail
                Whether to send an activation mail or not.
                If *False* the user will be saved as active.
        """
        if not is_valid_username(username):
            raise ValueError('invalid username')
        user = self.create_user(username, email, password)
        if not send_mail:
            # save the user as an active one
            user.status = User.STATUS_ACTIVE
            user.save()
            user.groups.add(Group.objects.get(name=settings.INYOKA_REGISTERED_GROUP_NAME))
        else:
            user.status = User.STATUS_INACTIVE
            send_activation_mail(user)
            user.save()
        return user

    def get_anonymous_user(self):
        return User.objects.get(username__iexact=settings.ANONYMOUS_USER_NAME)

    def get_system_user(self):
        """
        This returns the system user that is controlled by inyoka itself.  It
        is the sender for welcome notices, it updates the antispam list and
        is the owner for log entries in the wiki triggered by inyoka itself.
        """
        return User.objects.get(username__iexact=settings.INYOKA_SYSTEM_USER)


def upload_to_avatar(instance, filename):
    fn = 'portal/avatars/avatar_user%d.%s'
    return fn % (instance.pk, filename.rsplit('.', 1)[-1])


class User(AbstractBaseUser, PermissionsMixin, GuardianUserMixin):
    """User model that contains all information about a user."""
    STATUS_INACTIVE = 0
    STATUS_ACTIVE = 1
    STATUS_BANNED = 2
    STATUS_DELETED = 3
    STATUS_CHOICES = (
        (STATUS_INACTIVE, gettext_lazy('not yet activated')),
        (STATUS_ACTIVE, gettext_lazy('active')),
        (STATUS_BANNED, gettext_lazy('banned')),
        (STATUS_DELETED, gettext_lazy('deleted himself')),
    )
    #: Assign the `username` field
    USERNAME_FIELD = 'username'

    objects = UserManager()

    username = models.CharField(verbose_name=gettext_lazy('Username'),
                                max_length=30, unique=True, db_index=True)
    email = models.EmailField(verbose_name=gettext_lazy('Email address'),
                              unique=True, db_index=True)
    status = models.IntegerField(verbose_name=gettext_lazy('Activation status'),
                                 default=STATUS_INACTIVE,
                                 choices=STATUS_CHOICES)
    date_joined = models.DateTimeField(verbose_name=gettext_lazy('Member since'),
                                       default=datetime.utcnow)

    banned_until = models.DateTimeField(verbose_name=gettext_lazy('Banned until'),
                                        null=True, blank=True,
                                        help_text=gettext_lazy('leave empty to ban permanent'))

    # profile attributes
    avatar = models.ImageField(gettext_lazy('Avatar'), upload_to=upload_to_avatar,
                               blank=True, null=True)
    jabber = JabberField(gettext_lazy('Jabber'), max_length=200, blank=True)
    signature = InyokaMarkupField(verbose_name=gettext_lazy('Signature'), blank=True)
    location = models.CharField(gettext_lazy('Residence'), max_length=200, blank=True)
    gpgkey = models.CharField(gettext_lazy('GPG fingerprint'), max_length=255, blank=True)
    website = models.URLField(gettext_lazy('Website'), blank=True)
    launchpad = models.CharField(gettext_lazy('Launchpad username'), max_length=50, blank=True)
    settings = JSONField(gettext_lazy('Settings'), default={})

    # forum attribute
    forum_read_status = models.BinaryField(gettext_lazy('Read posts'), blank=True)

    # member title
    member_title = models.CharField(gettext_lazy('Team affiliation / Member title'),
                                    blank=True, null=True, max_length=200)

    # member icon
    icon = models.FilePathField(gettext_lazy('Group icon'),
                                path=os.path.join(inyoka_settings.MEDIA_ROOT, 'portal/team_icons'),
                                match=r'.*\.png', blank=True, null=True, recursive=True)

    def save(self, *args, **kwargs):
        """
        Save method that cleanups the cache after saving the model.
        """
        super().save(*args, **kwargs)
        cache.delete_many(['portal/user/%s' % self.id,
                           'user_permissions/%s' % self.id])

    def __str__(self):
        return self.username

    @transaction.atomic
    def rename(self, new_name, send_mail=True):
        """
        Rename method that checks for collision and if there is non,
        renames the users and if required sends a notification (default).
        Will raise a ValueError('invalid username') exception if user
        name is invalid.

        Returns True if the user is renamed or if the users current username is
        already new_name.

        Returns False if a user with the new_name already exists.
        """
        if not is_valid_username(new_name):
            raise ValueError('invalid username')
        if self.username == new_name:
            return True

        try:
            User.objects.get_by_username_or_email(new_name)
        except User.DoesNotExist:
            old_name = self.username
            self.username = new_name
            self.save()
            if send_mail:
                subject = _('Your user name on {sitename} has been changed to “{name}”') \
                    .format(name=escape(self.username), sitename=settings.BASE_DOMAIN_NAME)
                text = render_to_string('mails/account_rename.txt', {
                    'user': self,
                    'oldname': old_name,
                })
                self.email_user(subject, text, settings.INYOKA_SYSTEM_USER_EMAIL)
            return True
        else:
            return False

    @property
    def is_anonymous(self):
        return self.username == settings.ANONYMOUS_USER_NAME

    @property
    def is_authenticated(self):
        return not self.is_anonymous

    @property
    def is_active(self):
        return self.status == self.STATUS_ACTIVE

    @property
    def is_banned(self):
        return self.status == self.STATUS_BANNED

    @property
    def is_deleted(self):
        return self.status == self.STATUS_DELETED

    @property
    def is_inactive(self):
        return self.status == self.STATUS_INACTIVE

    @property
    def is_team_member(self):
        if self.is_anonymous:
            return False
        return self.groups.filter(name=settings.INYOKA_TEAM_GROUP_NAME).exists()

    def email_user(self, subject, message, from_email=None):
        """Sends an e-mail to this User."""
        send_mail(subject, message, from_email, [self.email])

    @deferred
    def _readstatus(self):
        from inyoka.forum.models import ReadStatus
        return ReadStatus(self.forum_read_status)

    @property
    def rendered_userpage(self):
        if hasattr(self, 'userpage'):
            return self.userpage.content_rendered
        else:
            return ""

    @property
    def launchpad_url(self):
        return 'http://launchpad.net/~%s' % escape(self.launchpad)

    @property
    def has_avatar(self):
        return self.avatar or self.settings.get('use_gravatar', False)

    @property
    def avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return self.gravatar_url

    @property
    def gravatar_url(self):
        if self.settings.get('use_gravatar', False):
            return get_gravatar(self.email)
        return None

    @property
    def jabber_url(self):
        return 'xmpp:%s' % escape(self.jabber)

    @property
    def icon_url(self):
        return href('media', self.icon)

    def get_absolute_url(self, action='show', *args, **query):
        if action == 'show':
            return href('portal', 'user', self.username, **query)
        elif action == 'privmsg':
            return href('portal', 'privmsg', 'new',
                        self.username, **query)
        elif action == 'activate':
            return href('portal', 'activate',
                        self.username, gen_activation_key(self), **query)
        elif action == 'activate_delete':
            return href('portal', 'delete',
                        self.username, gen_activation_key(self), **query)
        elif action == 'admin':
            return href('portal', 'user', self.username, 'edit', *args, **query)
        elif action in ('subscribe', 'unsubscribe'):
            return href('portal', 'user', self.username, action, **query)

    def has_content(self):
        """
        Returns True if the user has any content, else False.
        """
        return (self.post_count.value(calculate=False) or
                self.post_set.exists() or
                self.topics.exists() or
                self.comment_set.exists() or
                self.privatemessageentry_set.exists() or
                self.wiki_revisions.exists() or
                self.article_set.exists() or
                # Pastebin
                self.entry_set.exists() or
                self.event_set.exists() or
                self.suggestion_set.exists() or
                self.owned_suggestion_set.exists() or
                self.subscription_set.exists())

    @property
    def post_count(self):
        return QueryCounter(
            cache_key=f"user_post_count:{self.id}",
            query=self.post_set
                      .filter(hidden=False)
                      .filter(topic__forum__user_count_posts=True),
            use_task=True)

    def unban(self):
        """
        Check if a user is banned, either permanent or temporary and remove
        the ban if possible.

        Returns `True` if user is not banned or could be unbanned, or `False` otherwise.
        """
        if self.is_banned:
            # user banned ad infinite
            if self.banned_until is None:
                return False
            else:
                # user banned for a specific period of time
                if self.banned_until >= datetime.utcnow():
                    return False
                else:
                    # period of time gone, reset status
                    self.status = User.STATUS_ACTIVE
                    self.banned_until = None
                    self.save()
                    registered_group = Group.objects.get(name=settings.INYOKA_REGISTERED_GROUP_NAME)
                    self.groups.add(registered_group)
        return True

    def has_perm(self, perm, obj=None):
        """
        Heavy cached version of has_perm() to save many DB Queries.

        Stores cached Permissions inside our redis cache under /acl/<user.id> as JSON blob.
        """

        def obj_to_key(obj):
            return '%s-%s' % (obj.__class__.__name__.lower(), obj.id)

        cache_key = '/acl/%s' % self.id
        if not hasattr(self, 'perm_cache'):
            current_perm_cache = cache.get(cache_key, None)
            if current_perm_cache:
                self.perm_cache = loads(current_perm_cache)
            else:
                self.perm_cache = list(self.get_all_permissions())
                cache.set(cache_key, dumps(self.perm_cache))

        permkey = perm
        if obj:
            objkey = obj_to_key(obj)
            permkey = '%s-%s' % (objkey, perm)
            if objkey not in self.perm_cache:
                for permission in get_perms(self, obj):
                    self.perm_cache.append('%s-%s.%s' % (objkey, obj._meta.app_label, permission))
                self.perm_cache.append(objkey)
                cache.set(cache_key, dumps(self.perm_cache))

        return permkey in self.perm_cache

    def has_perms(self, perm_list, obj=None):
        """
        Simplified version of has_perms() to load permissions from perm_list in our has_perm()
        cache.

        Returns `True` if all permissions match, else `False`.
        """
        for perm in perm_list:
            if not self.has_perm(perm, obj):
                return False
        return True

    def set_random_password(self, length: int=32) -> None:
        alphabet = string.ascii_letters + string.digits
        password = ''.join(secrets.choice(alphabet) for i in range(length))

        self.set_password(password)

    backend = 'inyoka.portal.auth.InyokaAuthBackend'

    class Meta:
        permissions = (
            ('subscribe_user', 'Can subscribe Users'),
        )
        indexes = [
            models.Index(Upper('username'), name='upper_username_idx'),
        ]


class UserPage(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    content = InyokaMarkupField()


@receiver(user_logged_in)
def update_user_flags(sender, request, user, **kwargs):
    user.last_login = datetime.utcnow()
    user.save(update_fields=['last_login'])
    tz = user.settings.get('timezone')
    if tz and tz != settings.TIME_ZONE:
        request.session['django_timezone'] = tz


user_logged_in.disconnect(update_last_login)
