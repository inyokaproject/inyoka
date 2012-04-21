# -*- coding: utf-8 -*-
"""
    inyoka.portal.user
    ~~~~~~~~~~~~~~~~~~

    Our own user model used for implementing our own
    permission system and our own administration center.

    :copyright: (c) 2007-2012 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import os
import random
import string
from datetime import datetime
from os import path
from PIL import Image
from StringIO import StringIO

from django.conf import settings
from django.core.cache import cache
from django.core.files.storage import default_storage
from django.db import models
from django.utils.translation import ugettext_lazy, ugettext as _

from inyoka.utils import encode_confirm_data, classproperty
from inyoka.utils.decorators import deferred
from inyoka.utils.mail import send_mail
from inyoka.utils.html import escape
from inyoka.utils.user import normalize_username, get_hexdigest,\
    check_password, gen_activation_key
from inyoka.utils.local import current_request
from inyoka.utils.templating import render_template
from inyoka.utils.text import normalize_pagename
from inyoka.utils.gravatar import get_gravatar
from inyoka.utils.database import update_model, JSONField


UNUSABLE_PASSWORD = '!$!'
_ANONYMOUS_USER = _SYSTEM_USER = None
DEFAULT_GROUP_ID = 1 # group id for all registered users
PERMISSIONS = [(2 ** i, p[0], p[1]) for i, p in enumerate([
    ('admin_panel', u'Not in use anymore'), #TODO: DEPRECATED
    ('article_edit', ugettext_lazy(u'Ikhaya | can edit articles')),
    ('category_edit', ugettext_lazy(u'Ikhaya | can edit categories')),
    ('event_edit', ugettext_lazy(u'Ikhaya | can create new events')),
    ('comment_edit', ugettext_lazy(u'Ikhaya | can manage comments')),
    ('blog_edit', ugettext_lazy(u'Planet | can edit blogs')),
    ('configuration_edit', ugettext_lazy(u'Portal | can edit miscellaneous settings')),
    ('static_page_edit', ugettext_lazy(u'Portal | can edit static pages')),
    ('markup_css_edit', ugettext_lazy(u'Portal | can edit stylesheets')),
    ('static_file_edit', ugettext_lazy(u'Portal | can edit static files')),
    ('user_edit', ugettext_lazy(u'Portal | can edit users')),
    ('group_edit', ugettext_lazy(u'Portal | can edit groups')),
    ('send_group_pm', ugettext_lazy(u'Portal | can send messages to groups')),
    ('forum_edit', ugettext_lazy(u'Forum | can edit forums')),
    ('manage_topics', ugettext_lazy(u'Forum | can manage reported topics')),
    ('delete_topic', ugettext_lazy(u'Forum | can delete every topic and post')),
    ('article_read', ugettext_lazy(u'Ikhaya | can read unpublished articles')),
    ('manage_stats', ugettext_lazy(u'Admin | can manage statistics')),
    ('manage_pastebin', ugettext_lazy(u'Portal | can manage pastebin')),
    ('subscribe_to_users', ugettext_lazy(u'Portal | can watch users'))
])]
PERMISSION_NAMES = {val: desc for val, name, desc in PERMISSIONS}
PERMISSION_MAPPING = {name: val for val, name, desc in PERMISSIONS}

USER_STATUSES = {
    0: 'inactive', #not yet activated
    1: 'normal',
    2: 'banned',
    3: 'deleted', #deleted itself
}


class UserBanned(Exception):
    """
    Simple exception that is raised while
    log-in to give the user a somewhat detailed
    exception.
    """


def reactivate_user(id, email, status, time):
    from inyoka.wiki.models import Page as WikiPage

    if (datetime.utcnow() - time).days > 33:
        return {
            'failed': _(u'Sorry, more than one month passed since the deletion '
                        u'of the account'),
        }

    email_exists = User.objects.filter(email=email).exists()
    if email_exists:
        msg = _(u'This e-mail address is used by another user.')
        return {'failed': msg}

    user = User.objects.get(id=id)
    if not user.is_deleted:
        return {
            'failed': _(u'The account “%(name)s“ was already reactivated.') %
                {'name': escape(user.username)},
        }
    values = {'email': email,
              'status': status}
    if user.banned_until and user.banned_until < datetime.utcnow():
        values['status'] = 1
        values['banned_until'] = None

    update_model(user, **values)
    send_new_user_password(user)

    # reactivate user page
    try:
        userpage = WikiPage.objects.get_by_name('%s/%s' % (
                settings.WIKI_USER_BASE, escape(user.username)))
        userpage.edit(user=User.objects.get_system_user(), deleted=False,
                      note=_(u'The user “%(name)s“ has reactivated his account.')
                             % {'name': escape(user.username)})
    except WikiPage.DoesNotExist:
        pass

    return {
        'success': _(u'The account “%(name)s“ was reactivated. You will '
                     u'receive an email to set the new password.')
                     % {'name': escape(user.username)},
    }


def deactivate_user(user):
    """
    This deactivates a user and removes all personal information.
    To avoid abuse he is sent an email allowing him to reactivate the
    within the next month.
    """
    from inyoka.wiki.models import Page as WikiPage

    userdata = {
        'action': 'reactivate_user',
        'id': user.id,
        'email': user.email,
        'status': user.status,
        'time': datetime.utcnow(),
    }

    userdata = encode_confirm_data(userdata)

    subject = _(u'Deactivation of your account “%(name)s“ on %(sitename)s') \
                % {'name': escape(user.username),
                   'sitename': settings.BASE_DOMAIN_NAME}
    text = render_template('mails/account_deactivate.txt', {
        'user': user,
        'userdata': userdata,
    })
    user.email_user(subject, text, settings.INYOKA_SYSTEM_USER_EMAIL)

    # delete user wiki page
    try:
        userpage = WikiPage.objects.get_by_name('%s/%s' % (
                settings.WIKI_USER_BASE, escape(user.username)))
        userpage.edit(user=User.objects.get_system_user(), deleted=True,
                      note=_(u'The user “%(name)s“ has deactivated his account.')
                             % {'name': escape(user.username)})
    except WikiPage.DoesNotExist:
        pass

    user.status = 3
    if not user.is_banned:
        user.email = 'user%d@ubuntuusers.de.invalid' % user.id
    user.set_unusable_password()
    user.groups.remove(*user.groups.all())
    user.avatar = user.coordinates_long = user.coordinates_lat = \
        user.new_password_key = user._primary_group = None
    user.icq = user.jabber = user.msn = user.aim = user.yim = user.skype = \
        user.wengophone = user.sip = user.location = user.signature = \
        user.gpgkey = user.location = user.occupation = user.interests = \
        user.website = user.launchpad = user.member_title = ''
    user.save()



def send_new_email_confirmation(user, email):
    """Send the user an email where he can confirm his new email address"""
    data = {
        'action': 'set_new_email',
        'id': user.id,
        'email': email,
        'time': datetime.utcnow()
    }

    text = render_template('mails/new_email_confirmation.txt', {
        'user': user,
        'data': encode_confirm_data(data),
    })
    subject = _(u'%(sitename)s – Confirm email address') \
              % {'sitename': settings.BASE_DOMAIN_NAME}
    send_mail(subject, text, settings.INYOKA_SYSTEM_USER_EMAIL, [email])


def set_new_email(id, email, time):
    """
    Save the new email address the user has confirmed, and send an email to
    his old address where he can reset it to protect against abuse.
    """
    if (datetime.utcnow() - time).days > 8:
        return {'failed': _(u'The link is too old.')}
    user = User.objects.get(id=id)

    data = {
        'action': 'reset_email',
        'id': user.id,
        'email': user.email,
        'time': datetime.utcnow(),
    }
    text = render_template('mails/reset_email.txt', {
        'user': user,
        'new_email': email,
        'data': encode_confirm_data(data),
    })
    subject = _(u'%(sitename)s – Email address changed') \
              % {'sitename': settings.BASE_DOMAIN_NAME}
    user.email_user(subject, text, settings.INYOKA_SYSTEM_USER_EMAIL)

    user.email = email
    user.save()
    return {
        'success': _(u'Your new email address was saved.')
    }


def reset_email(id, email, time):
    if (datetime.utcnow() - time).days > 33:
        return {'failed': _(u'The link is too old.')}

    user = User.objects.get(id=id)
    user.email = email
    user.save()

    return {
        'success': _('Your email address was reset.')
    }

def send_activation_mail(user):
    """send an activation mail"""
    message = render_template('mails/activation_mail.txt', {
        'user':             user,
        'email':            user.email,
        'activation_key':   gen_activation_key(user)
    })
    subject = _(u'%(sitename)s – Activation of the user “%(name)s“') \
              % {'sitename': settings.BASE_DOMAIN_NAME,
                 'name': user.username}
    send_mail(subject, message, settings.INYOKA_SYSTEM_USER_EMAIL, [user.email])


def send_new_user_password(user):
    new_password_key = ''.join(random.choice(string.lowercase + string.digits)
                               for _ in range(24))
    user.new_password_key = new_password_key
    user.save()
    message = render_template('mails/new_user_password.txt', {
        'username':         user.username,
        'email':            user.email,
        'new_password_url': href('portal', 'lost_password',
                                 user.urlsafe_username, new_password_key),
    })
    subject = _(u'%(sitename)s – New password for “%(name)s“') \
              % {'sitename': settings.BASE_DOMAIN_NAME,
                 'name': user.username}
    send_mail(subject, message, settings.INYOKA_SYSTEM_USER_EMAIL, [user.email])


class Group(models.Model):
    name = models.CharField('Name', max_length=80, unique=True, db_index=True)
    is_public = models.BooleanField(ugettext_lazy(u'Public profile'))
    _default_group = None
    permissions = models.IntegerField(ugettext_lazy(u'Privileges'), default=0)
    icon = models.ImageField(ugettext_lazy(u'Team icon'),
                             upload_to='portal/team_icons',
                             blank=True, null=True)

    @property
    def icon_url(self):
        if not self.icon:
            return None
        return self.icon.url

    def save_icon(self, img):
        """
        Save `img` to the file system.

        :return: a boolean if the `img` was resized or not.
        """
        data = img.read()
        image = Image.open(StringIO(data))
        fn = 'portal/team_icons/team_%s.%s' % (self.name, image.format.lower())
        image_path = path.join(settings.MEDIA_ROOT, fn)
        # clear the file system
        if self.icon:
            self.icon.delete(save=False)

        std = storage.get_many(('team_icon_height', 'team_icon_width'))
        max_size = (int(std['team_icon_height']),
                    int(std['team_icon_width']))
        resized = False
        if image.size > max_size:
            image = image.resize(max_size)
            image.save(image_path)
            resized = True
        else:
            image.save(image_path)
        self.icon = fn

        return resized

    def get_absolute_url(self, action=None):
        if action == 'edit':
            return href('portal', 'group', self.name, 'edit')
        return href('portal', 'group', self.name)

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return unicode(self).encode('utf-8')

    @classmethod
    def get_default_group(self):
        """Return a default group for all registered users."""
        if not Group._default_group:
            Group._default_group = Group.objects.get(id=DEFAULT_GROUP_ID)
        return Group._default_group


class UserManager(models.Manager):

    def get(self, pk=None, **kwargs):
        if 'username' in kwargs:
            kwargs['username'] = normalize_username(kwargs['username'])

        if isinstance(pk, basestring):
            try:
                normalized = normalize_username(pk)
                return User.objects.get(username__iexact=normalized, **kwargs)
            except (ValueError, User.DoesNotExist):
                try:
                    return User.objects.get(username__iexact=pk, **kwargs)
                except User.DoesNotExist:
                    return User.objects.get(username__iexact=pk.replace('_', ' '))

        if pk is None:
            pk = kwargs.pop('id__exact', None)
        if pk is not None:
            pk = int(pk)
            user = cache.get('portal/user/%d' % pk)
            if user is not None:
                return user
            kwargs['pk'] = pk
        user = models.Manager.get(self, **kwargs)
        if pk is not None:
            cache.set('portal/user/%d' % pk, user, 300)
        return user

    def get_by_username_or_email(self, name):
        """Get a user by it's username or email address"""
        try:
            user = User.objects.get(name)
        except User.DoesNotExist, exc:
            # fallback to email
            if '@' in name:
                user = User.objects.get(email__iexact=name)
            else:
                raise exc
        return user

    def create_user(self, username, email, password=None):
        now = datetime.utcnow()
        user = self.model(
            None, username,
            email.strip().lower(),
            'placeholder', False,
            now, now
        )
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
        user = self.create_user(normalize_username(username), email, password)
        if not send_mail:
            # save the user as an active one
            user.status = 1
        else:
            user.status = 0
            send_activation_mail(user)
        user.save()
        return user

    def logout(self, request):
        request.session.pop('uid', None)
        request.user = self.get_anonymous_user()

    def authenticate(self, username, password):
        """
        Authenticate a user with `username` (which can also be the email
        address) and `password`.

        :Raises:
            User.DoesNotExist
                If the user with `username` does not exist
            UserBanned
                If the found user was banned by an admin.
        """
        try:
            user = User.objects.get(username)
        except User.DoesNotExist, exc:
            # fallback to email login
            if '@' in username:
                user = User.objects.get(email__iexact=username)
            else:
                raise exc

        if user.is_banned:
            # gebannt für immer…
            if user.banned_until is None:
                raise UserBanned()
            else:
                # gebannt für zeitraum
                if (user.banned_until >= datetime.utcnow()):
                    raise UserBanned()
                else:
                    # zeitraum vorbei, bann zurücksetzen
                    user.status = 1
                    user.banned_until = None
                    user.save()

        if user.check_password(password, auto_convert=True):
            return user

    def get_anonymous_user(self):
        global _ANONYMOUS_USER
        if not _ANONYMOUS_USER:
            name = settings.INYOKA_ANONYMOUS_USER
            try:
                user = User.objects.get(username=name)
            except User.DoesNotExist:
                user = self.create_user(name, name)
            _ANONYMOUS_USER = user
        return _ANONYMOUS_USER

    def get_system_user(self):
        """
        This returns the system user that is controlled by inyoka itself.  It
        is the sender for welcome notices, it updates the antispam list and
        is the owner for log entries in the wiki triggered by inyoka itself.
        """
        global _SYSTEM_USER
        if not _SYSTEM_USER:
            name = settings.INYOKA_SYSTEM_USER
            try:
                user = User.objects.get(username=name)
            except User.DoesNotExist:
                user = self.create_user(name, name)
            _SYSTEM_USER = user
        return _SYSTEM_USER


class User(models.Model):
    """User model that contains all informations about an user."""
    objects = UserManager()

    username = models.CharField(ugettext_lazy(u'Username'),
                                max_length=30, unique=True, db_index=True)
    email = models.EmailField(ugettext_lazy(u'Email address'),
                              unique=True, max_length=50, db_index=True)
    password = models.CharField(ugettext_lazy(u'Password'), max_length=128)
    status = models.IntegerField(ugettext_lazy(u'Status'), default=0)
    last_login = models.DateTimeField(ugettext_lazy(u'Last login'),
                                      default=datetime.utcnow)
    date_joined = models.DateTimeField(ugettext_lazy(u'Member since'),
                                       default=datetime.utcnow)
    groups = models.ManyToManyField(Group,
                                    verbose_name=ugettext_lazy(u'Groups'),
                                    blank=True,
                                    related_name='user_set')
    new_password_key = models.CharField(ugettext_lazy(u'Confirmation key for a new password'),
                                        blank=True, null=True, max_length=32)

    banned_until = models.DateTimeField(ugettext_lazy(u'Banned until'), null=True)

    # profile attributes
    post_count = models.IntegerField(ugettext_lazy(u'Posts'), default=0)
    avatar = models.ImageField(ugettext_lazy(u'Avatar'), upload_to='portal/avatars',
                               blank=True, null=True)
    jabber = models.CharField(ugettext_lazy(u'Jabber'), max_length=200, blank=True)
    icq = models.CharField(ugettext_lazy(u'ICQ'), max_length=16, blank=True)
    msn = models.CharField(ugettext_lazy(u'MSN'), max_length=200, blank=True)
    aim = models.CharField(ugettext_lazy(u'AIM'), max_length=200, blank=True)
    yim = models.CharField(ugettext_lazy(u'Yahoo Messenger'), max_length=200, blank=True)
    skype = models.CharField(ugettext_lazy(u'Skype'), max_length=200, blank=True)
    wengophone = models.CharField(ugettext_lazy(u'WengoPhone'), max_length=200, blank=True)
    sip = models.CharField('SIP', max_length=200, blank=True)
    signature = models.TextField(ugettext_lazy(u'Signature'), blank=True)
    coordinates_long = models.FloatField(ugettext_lazy(u'Coordinates (longitude)'), blank=True, null=True)
    coordinates_lat = models.FloatField(ugettext_lazy(u'Coordinates (latitude)'), blank=True, null=True)
    location = models.CharField(ugettext_lazy(u'Residence'), max_length=200, blank=True)
    gpgkey = models.CharField(ugettext_lazy(u'GPG key'), max_length=8, blank=True)
    occupation = models.CharField(ugettext_lazy(u'Job'), max_length=200, blank=True)
    interests = models.CharField(ugettext_lazy(u'Interests'), max_length=200, blank=True)
    website = models.URLField(ugettext_lazy(u'Website'), blank=True)
    launchpad = models.CharField(ugettext_lazy(u'Launchpad username'), max_length=50, blank=True)
    settings = JSONField(ugettext_lazy(u'Settings'), default={})
    _permissions = models.IntegerField(ugettext_lazy(u'Privileges'), default=0)

    # forum attribues
    forum_last_read = models.IntegerField(ugettext_lazy(u'Last read post'),
                                          default=0, blank=True)
    forum_read_status = models.TextField(ugettext_lazy(u'Read posts'), blank=True)
    forum_welcome = models.TextField(ugettext_lazy(u'Read welcome message'),
                                     blank=True)

    # member title
    member_title = models.CharField(ugettext_lazy(u'Member title'), blank=True, null=True,
                                    max_length=200)

    # primary group from which the user gets some settings
    # e.g the membericon
    _primary_group = models.ForeignKey(Group, related_name='primary_users_set',
                                       blank=True, null=True,
                                       db_column='primary_group_id')

    def save(self, *args, **kwargs):
        """
        Save method that dumps `self.settings` before and cleanup
        the cache after saving the model.
        """
        super(User, self).save(*args, **kwargs)
        cache.delete('portal/user/%s/signature' % self.id)
        cache.delete('portal/user/%s' % self.id)

    def __unicode__(self):
        return self.username

    is_anonymous = property(lambda x: x.username == settings.INYOKA_ANONYMOUS_USER)
    is_authenticated = property(lambda x: not x.is_anonymous)
    is_active = property(lambda x: x.status == 1)
    is_banned = property(lambda x: x.status == 2)
    is_deleted = property(lambda x: x.status == 3)

    def set_password(self, raw_password):
        """Set a new sha1 generated password hash"""
        salt = get_hexdigest(str(random.random()), str(random.random()))[:5]
        hsh = get_hexdigest(salt, raw_password)
        self.password = '%s$%s' % (salt, hsh)
        # invalidate the new_password_key
        if self.new_password_key:
            self.new_password_key = None

    def check_password(self, raw_password, auto_convert=False):
        """
        Returns a boolean of whether the raw_password was correct.
        """
        return check_password(raw_password, self.password,
                              convert_user=auto_convert and self or False)

    def set_unusable_password(self):
        """Sets a value that will never be a valid hash"""
        self.password = UNUSABLE_PASSWORD

    def has_usable_password(self):
        return self.password != UNUSABLE_PASSWORD

    @property
    def has_wikipage(self):
        """
        Returns the rendered wikipage if it exists, otherwise None
        """
        from inyoka.wiki.models import Page as WikiPage
        key = '%s/%s' % (settings.WIKI_USER_BASE,
                         normalize_pagename(self.username))
        return WikiPage.objects.exists(key)

    def email_user(self, subject, message, from_email=None):
        """Sends an e-mail to this User."""
        send_mail(subject, message, from_email, [self.email])

    def get_groups(self):
        """Get groups inclusive the default group for registered users"""
        groups = self.is_authenticated and [Group.get_default_group()] or []
        groups.extend(self.groups.all())
        return groups

    @deferred
    def permissions(self):
        if not self.is_authenticated:
            return 0
        key = 'user_permissions/%s' % self.id
        result = cache.get(key)
        if result is None:
            result = self._permissions
            for group in self.groups.all():
                result |= group.permissions
            cache.set(key, result)
        return result

    def can(self, name):
        """
        Return a boolean whether the user has a special privilege.
        """
        return bool(PERMISSION_MAPPING[name] & self.permissions)

    @deferred
    def primary_group(self):
        # FIXME:
        # primary_group is currently only used to display the teammembers
        # icons, not checking self.groups saves shitloads of queries
        #if self._primary_group is None:
        #    # we use the first assigned group as the primary one
        #    groups = self.groups.all()
        #    if len(groups) >= 1:
        #        return groups[0]
        #    else:
        #        return None
        return self._primary_group

    @deferred
    def _readstatus(self):
        from inyoka.forum.models import ReadStatus
        return ReadStatus(self.forum_read_status)

    @property
    def rendered_signature(self):
        return self.render_signature()

    def render_signature(self, request=None, format='html', nocache=False):
        """Render the user signature and cache it if `nocache` is `False`."""
        if request is None:
            request = current_request._get_current_object()
        context = RenderContext(request, simplified=True)
        if nocache or self.id is None or format != 'html':
            return parse(self.signature).render(context, format)
        key = 'portal/user/%d/signature' % self.id
        instructions = cache.get(key)
        if instructions is None:
            instructions = parse(self.signature).compile(format)
            cache.set(key, instructions)
        return render(instructions, context)

    @property
    def launchpad_url(self):
        return u'http://launchpad.net/~%s' % escape(self.launchpad)

    @property
    def has_avatar(self):
        return self.avatar or self.settings.get('use_gravatar', False)

    @property
    def avatar_url(self):
        gravatar = self.settings.get('use_gravatar', False)
        if not self.avatar and not gravatar:
            return href('static', 'img', 'portal', 'no_avatar.png')
        elif gravatar and not self.avatar:
            return self.gravatar_url
        return self.avatar.url

    @property
    def gravatar_url(self):
        if not self.settings.get('use_gravatar', False):
            return href('static', 'img', 'portal', 'no_avatar.png')
        return get_gravatar(self.email)

    @property
    def jabber_url(self):
        return u'xmpp:%s' % escape(self.jabber)

    @property
    def urlsafe_username(self):
        '''return the username with space replaced by _ for urls'''
        return self.username.replace(' ', '_')

    def save_avatar(self, img):
        """
        Save `img` to the file system.

        :return: boolean value if `img` was resized or not.
        """
        data = img.read()
        image = Image.open(StringIO(data))
        fn = 'portal/avatars/avatar_user%d.%s' % (self.id,
             image.format.lower())
        #: clear the file system
        self.delete_avatar()

        std = storage.get_many(('max_avatar_height', 'max_avatar_width'))
        max_size = (int(std['max_avatar_height']),
                    int(std['max_avatar_width']))
        resized = False
        if image.size > max_size:
            image = image.resize(max_size)
            image_path = path.join(settings.MEDIA_ROOT, fn)
            image.save(image_path)
            resized = True
        else:
            img.seek(0)
            default_storage.save(fn, img)
        self.avatar = fn

        return resized

    def delete_avatar(self):
        """Delete the avatar from the file system."""
        self.avatar.delete(save=False)

    def get_absolute_url(self, action='show', *args):
        if action == 'show':
            return href('portal', 'user', self.urlsafe_username)
        elif action == 'privmsg':
            return href('portal', 'privmsg', 'new',
                        self.urlsafe_username)
        elif action == 'activate':
            return href('portal', 'activate',
                        self.urlsafe_username, gen_activation_key(self))
        elif action == 'activate_delete':
            return href('portal', 'delete',
                        self.urlsafe_username, gen_activation_key(self))
        elif action == 'admin':
            return href('portal', 'user', self.urlsafe_username, 'edit', *args)
        elif action in ('subscribe', 'unsubscribe'):
            return href('portal', 'user', self.urlsafe_username, action)

    def login(self, request):
        self.last_login = datetime.utcnow()
        request.session['uid'] = self.id
        request.session.pop('_sk', None)
        request.user = self
        # invalidate the new_password_key
        if self.new_password_key:
            self.new_password_key = None
        self.save()

    def get_and_delete_messages(self, *args, **kwargs):
        """Stub for to fix openid integration as it's calling the django.messages API"""
        #TODO: this method does not exist in Django 1.4 anymore, so remove it if we upgrade!
        return []

    @classproperty
    def SYSTEM_USER(cls):
        return cls.objects.get_system_user()

    @classproperty
    def ANONYMOUS_USER(cls):
        return cls.objects.get_anonymous_user()


class UserData(models.Model):
    user = models.ForeignKey(User)
    key = models.CharField(max_length=255)
    value = models.CharField(max_length=255)


# circ imports
from inyoka.wiki.parser import parse, render, RenderContext
from inyoka.utils.urls import href
from inyoka.utils.storage import storage
