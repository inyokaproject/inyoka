# -*- coding: utf-8 -*-
"""
    inyoka.portal.user
    ~~~~~~~~~~~~~~~~~~

    Our own user model used for implementing our own
    permission system and our own administration center.

    :copyright: (c) 2007-2016 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    Group,
    update_last_login,
)
from django.contrib.auth.signals import user_logged_in
from django.core import signing
from django.core.cache import cache
from django.db import models, transaction
from django.dispatch import receiver
from django.utils.html import escape
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy

from inyoka.utils.cache import QueryCounter
from inyoka.utils.database import InyokaMarkupField, JSONField
from inyoka.utils.decorators import deferred
from inyoka.utils.gravatar import get_gravatar
from inyoka.utils.mail import send_mail
from inyoka.utils.templating import render_template
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
        msg = _(u'This e-mail address is used by another user.')
        return {'failed': msg}

    user = User.objects.get(id=id)
    if not user.is_deleted:
        return {
            'failed': _(u'The account “%(name)s” was already reactivated.') %
               {'name': escape(user.username)},
        }
    user.email = email
    user.status = status

    if user.banned_until and user.banned_until < datetime.utcnow():
        # User was banned but the ban time exceeded
        user.status = User.STATUS_ACTIVE
        user.banned_until = None

    # Set a dumy password
    user.set_password(User.objects.make_random_password(length=32))
    user.save()

    # Enforce registered group if active.
    if user.status == User.STATUS_ACTIVE:
        user.groups.add(Group.objects.get_registered_group())

    return {
        'success': _(u'The account “%(name)s” was reactivated. Please use the '
                     u'password recovery function to set a new password.')
        % {'name': escape(user.username)},
    }


def deactivate_user(user):
    """
    This deactivates a user and removes all personal information.
    To avoid abuse he is sent an email allowing him to reactivate the
    within the next month.
    """

    data = {
        'id': user.id,
        'email': user.email,
        'status': user.status,
    }

    subject = _(u'Deactivation of your account “%(name)s” on %(sitename)s') % {
        'name': escape(user.username),
        'sitename': settings.BASE_DOMAIN_NAME}
    text = render_template('mails/account_deactivate.txt', {
        'user': user,
        'data': signing.dumps(data, salt='inyoka.action.reactivate_user'),
    })
    user.email_user(subject, text, settings.INYOKA_SYSTEM_USER_EMAIL)

    user.status = User.STATUS_DELETED
    if not user.is_banned:
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

    text = render_template('mails/new_email_confirmation.txt', {
        'user': user,
        'data': signing.dumps(data, salt='inyoka.action.set_new_email'),
    })
    subject = _(u'%(sitename)s – Confirm email address') % {
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
    text = render_template('mails/reset_email.txt', {
        'user': user,
        'new_email': email,
        'data': signing.dumps(data, salt='inyoka.action.reset_email'),
    })
    subject = _(u'%(sitename)s – Email address changed') % {
        'sitename': settings.BASE_DOMAIN_NAME
    }
    user.email_user(subject, text, settings.INYOKA_SYSTEM_USER_EMAIL)

    user.email = email
    user.save()
    return {
        'success': _(u'Your new email address was saved.')
    }


def reset_email(id, email):
    user = User.objects.get(id=id)
    user.email = email
    user.save()

    return {
        'success': _(u'Your email address was reset.')
    }


def send_activation_mail(user):
    """send an activation mail"""
    message = render_template('mails/activation_mail.txt', {
        'user': user,
        'email': user.email,
        'activation_key': gen_activation_key(user)
    })
    subject = _(u'%(sitename)s – Activation of the user “%(name)s”') % {
        'sitename': settings.BASE_DOMAIN_NAME,
        'name': user.username}
    send_mail(subject, message, settings.INYOKA_SYSTEM_USER_EMAIL, [user.email])


class UserManager(BaseUserManager):
    def get_by_username_or_email(self, name):
        """Get a user by it's username or email address"""
        try:
            user = User.objects.get(username__iexact=name)
        except User.DoesNotExist as exc:
            # fallback to email
            if '@' in name:
                user = User.objects.get(email__iexact=name)
            else:
                raise exc
        return user

    def create_user(self, username, email, password=None, system=False):
        now = datetime.utcnow()
        user = self.model(username=username, email=email.strip().lower(),
            status=0, date_joined=now, last_login=now, system=system)
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
            user.groups.add(Group.objects.get_registered_group())
        else:
            user.status = User.STATUS_INACTIVE
            send_activation_mail(user)
            user.save()
        return user

    def get_anonymous_user(self):
        return User.objects.get(username__iexact=settings.INYOKA_ANONYMOUS_USER)

    def get_system_user(self):
        """
        This returns the system user that is controlled by inyoka itself.  It
        is the sender for welcome notices, it updates the antispam list and
        is the owner for log entries in the wiki triggered by inyoka itself.
        """
        return User.objects.get(username__iexact=settings.INYOKA_SYSTEM_USER)

    def create_system_users(self):
        """
        Creates the required system User as defined in INYOKA_SYSTEM_USER and
        INYOKA_ANYONYMOUS_USER. This is only useful in unit tests and as
        management command.
        """
        def get_or_create(username):
            try:
                return User.objects.get(username__iexact=username)
            except User.DoesNotExist:
                return User.objects.create_user(username, username)

        user = get_or_create(settings.INYOKA_ANONYMOUS_USER)
        user.system = True
        user.save()
        group = Group.objects.get(name__iexact=settings.INYOKA_ANONYMOUS_GROUP_NAME)
        user.groups.clear()
        user.groups.add(group)

        user = get_or_create(settings.INYOKA_SYSTEM_USER)
        user.system = True
        user.save()


def upload_to_avatar(instance, filename):
    fn = 'portal/avatars/avatar_user%d.%s'
    return fn % (instance.pk, filename.rsplit('.', 1)[-1])


class User(AbstractBaseUser):
    """User model that contains all informations about an user."""
    STATUS_INACTIVE = 0
    STATUS_ACTIVE = 1
    STATUS_BANNED = 2
    STATUS_DELETED = 3
    STATUS_CHOICES = (
        (STATUS_INACTIVE, ugettext_lazy(u'not yet activated')),
        (STATUS_ACTIVE, ugettext_lazy(u'active')),
        (STATUS_BANNED, ugettext_lazy(u'banned')),
        (STATUS_DELETED, ugettext_lazy(u'deleted himself')),
    )
    #: Assign the `username` field
    USERNAME_FIELD = 'username'

    objects = UserManager()

    username = models.CharField(verbose_name=ugettext_lazy(u'Username'),
                                max_length=30, unique=True, db_index=True)
    email = models.EmailField(verbose_name=ugettext_lazy(u'Email address'),
                              unique=True, db_index=True)
    status = models.IntegerField(verbose_name=ugettext_lazy(u'Activation status'),
                                 default=STATUS_INACTIVE,
                                 choices=STATUS_CHOICES)
    system = models.BooleanField(verbose_name=ugettext_lazy(u'System user'),
                                 default=False,
                                 null=False)
    date_joined = models.DateTimeField(verbose_name=ugettext_lazy(u'Member since'),
                                       default=datetime.utcnow)
    groups = models.ManyToManyField(Group,
                                    verbose_name=ugettext_lazy(u'Groups'),
                                    blank=True,
                                    related_name='user_set')

    banned_until = models.DateTimeField(verbose_name=ugettext_lazy(u'Banned until'),
                                        null=True, blank=True,
                                        help_text=ugettext_lazy(u'leave empty to ban permanent'))

    # profile attributes
    avatar = models.ImageField(ugettext_lazy(u'Avatar'), upload_to=upload_to_avatar,
                               blank=True, null=True)
    jabber = models.CharField(ugettext_lazy(u'Jabber'), max_length=200, blank=True)
    signature = InyokaMarkupField(verbose_name=ugettext_lazy(u'Signature'), blank=True)
    location = models.CharField(ugettext_lazy(u'Residence'), max_length=200, blank=True)
    gpgkey = models.CharField(ugettext_lazy(u'GPG key'), max_length=255, blank=True)
    website = models.URLField(ugettext_lazy(u'Website'), blank=True)
    launchpad = models.CharField(ugettext_lazy(u'Launchpad username'), max_length=50, blank=True)
    settings = JSONField(ugettext_lazy(u'Settings'), default={})

    # forum attribues
    forum_last_read = models.IntegerField(ugettext_lazy(u'Last read post'),
                                          default=0, blank=True)
    forum_read_status = models.TextField(ugettext_lazy(u'Read posts'), blank=True)

    # member title
    member_title = models.CharField(ugettext_lazy(u'Team affiliation / Member title'),
                                    blank=True, null=True, max_length=200)

    # member icon
    icon = models.ImageField(ugettext_lazy(u'Team icon'),
                             upload_to='portal/team_icons',
                             blank=True, null=True)

    def save(self, *args, **kwargs):
        """
        Save method that dumps `self.settings` before and cleanup
        the cache after saving the model.
        """
        super(User, self).save(*args, **kwargs)
        cache.delete_many(['portal/user/%s' % self.id,
                           'user_permissions/%s' % self.id])

    def __unicode__(self):
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
                subject = _(u'Your user name on {sitename} has been changed to “{name}”') \
                    .format(name=escape(self.username), sitename=settings.BASE_DOMAIN_NAME)
                text = render_template('mails/account_rename.txt', {
                    'user': self,
                    'oldname': old_name,
                })
                self.email_user(subject, text, settings.INYOKA_SYSTEM_USER_EMAIL)
            return True
        else:
            return False

    @property
    def is_anonymous(self):
        return self.username == settings.INYOKA_ANONYMOUS_USER

    def is_authenticated(self):
        # Not a property to be compatible with django.
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

    def email_user(self, subject, message, from_email=None):
        """Sends an e-mail to this User."""
        send_mail(subject, message, from_email, [self.email])

# FIXME: Entering Danger Zone!
    def permissions(self):
        return 65536

    def can(self, name):
        return True

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
        return u'http://launchpad.net/~%s' % escape(self.launchpad)

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
        return u'xmpp:%s' % escape(self.jabber)

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
            cache_key="user_post_count:{}".format(self.id),
            query=self.post_set
                      .filter(hidden=False)
                      .filter(topic__forum__user_count_posts=True),
            use_task=True)

    # TODO: reevaluate if needed.
    backend = 'inyoka.portal.auth.InyokaAuthBackend'


class UserPage(models.Model):
    user = models.OneToOneField(User)
    content = InyokaMarkupField()


@receiver(user_logged_in)
def update_user_flags(sender, request, user, **kwargs):
    user.last_login = datetime.utcnow()
    user.save(update_fields=['last_login'])
    tz = user.settings.get('timezone')
    if tz and tz != settings.TIME_ZONE:
        request.session['django_timezone'] = tz

user_logged_in.disconnect(update_last_login)
