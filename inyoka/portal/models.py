"""
    inyoka.portal.models
    ~~~~~~~~~~~~~~~~~~~~

    Models for the portal.

    :copyright: (c) 2007-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import os
import glob
import gzip
import hashlib

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType, ContentTypeManager
from django.core.cache import cache
from django.core.validators import RegexValidator
from django.db import models, transaction
from django.utils.translation import gettext_lazy
from django.utils.functional import cached_property

from .user import User
from inyoka.utils.database import InyokaMarkupField
from inyoka.utils.urls import href
from inyoka.wiki.acl import has_privilege as have_wiki_privilege


class SubscriptionManager(ContentTypeManager):
    """
    Manager class for the `Subscription` model.
    """

    def _get_filter(self, user, object, ctype_query):
        if ctype_query is not None:
            ctype = ContentType.objects.get_by_natural_key(*ctype_query)
        else:
            ctype = ContentType.objects.get_for_model(object)
        filter = {'content_type': ctype, 'user': user}

        if object:
            filter['object_id'] = object.id

        return filter

    def user_subscribed(self, user, object, ctype_query=None, clear_notified=False):
        """Return `True` or `False` whether the user has subscribed or not"""
        if user.is_anonymous:
            return False
        filter = self._get_filter(user, object, ctype_query)

        notifies = Subscription.objects.filter(**filter)\
                                       .values_list('notified', flat=True)[:1]
        notified = bool(notifies and notifies[0])
        if clear_notified and notified:
            Subscription.objects.filter(**filter).update(notified=False)
        return bool(notifies)

    def get_for_user(self, user, object, ctype_query=None):
        filter = self._get_filter(user, object, ctype_query)
        return Subscription.objects.get(**filter)

    @classmethod
    def delete_list(cls, user_id, ids):
        if not ids:
            return
        ids = [int(id) for id in ids]
        Subscription.objects.filter(id__in=ids, user__id=int(user_id)).delete()

    @classmethod
    def mark_read_list(cls, user_id, ids):
        if not ids:
            return
        ids = [int(id) for id in ids]
        Subscription.objects.filter(id__in=ids, user__id=int(user_id))\
                            .update(notified=0)


PRIVMSG_FOLDERS_DATA = (
    (0, 'sent', gettext_lazy('Sent')),
    (1, 'inbox', gettext_lazy('Inbox')),
    (2, 'trash', gettext_lazy('Trash')),
    (3, 'archive', gettext_lazy('Archive')))


PRIVMSG_FOLDERS = {}
for folder in PRIVMSG_FOLDERS_DATA:
    PRIVMSG_FOLDERS[folder[0]] = PRIVMSG_FOLDERS[folder[1]] = folder


class PrivateMessage(models.Model):
    """
    Private messages allow users to communicate with each other privately.
    This model represent one of these messages.
    """
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.CharField(gettext_lazy('Title'), max_length=255)
    pub_date = models.DateTimeField(gettext_lazy('Date'))
    text = InyokaMarkupField(verbose_name=gettext_lazy('Text'), application='portal')

    class Meta:
        ordering = ('-pub_date',)
        permissions = (
            ('send_group_privatemessage', 'Can send Group Private Messages'),
        )

    def send(self, recipients):
        self.save()
        PrivateMessageEntry(message=self, user=self.author, read=True,
                            folder=PRIVMSG_FOLDERS['sent'][0]).save()
        for recipient in recipients:
            cache.delete(f'portal/pm_count/{recipient.id}')
            PrivateMessageEntry(message=self, user=recipient, read=False,
                                folder=PRIVMSG_FOLDERS['inbox'][0]).save()

    @property
    def recipients(self):
        if not hasattr(self, '_recipients'):
            entries = PrivateMessageEntry.objects.filter(message=self) \
                .exclude(user=self.author).select_related('user')
            self._recipients = [e.user for e in entries]
        return self._recipients

    @property
    def author_avatar(self):
        return self.author.get_profile()

    def get_absolute_url(self, action='show'):
        if action == 'show':
            return href('portal', 'privmsg', self.id)
        elif action == 'reply':
            return href('portal', 'privmsg', 'new', reply_to=self.id)
        elif action == 'reply_to_all':
            return href('portal', 'privmsg', 'new', reply_to_all=self.id)
        elif action == 'forward':
            return href('portal', 'privmsg', 'new', forward=self.id)


class PrivateMessageEntry(models.Model):
    """
    A personal entry for each person who is affected by the private
    message.  This entry can be moved between folders and stores the
    read status flag.
    """
    message = models.ForeignKey('PrivateMessage', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    read = models.BooleanField(gettext_lazy('Read'), default=False)
    folder = models.SmallIntegerField(gettext_lazy('Folder'),
        null=True,
        choices=[(f[0], f[1]) for f in PRIVMSG_FOLDERS_DATA])

    @property
    def folder_name(self):
        return PRIVMSG_FOLDERS[self.folder][2]

    @property
    def is_own_message(self):
        return self.user.id == self.message.author.id

    @property
    def in_archive(self):
        return self.folder == PRIVMSG_FOLDERS['archive'][0]

    def get_absolute_url(self, action='view'):
        if action == 'view':
            return href('portal', 'privmsg', PRIVMSG_FOLDERS[self.folder][1],
                        self.id)
        elif action == 'reply':
            return href('portal', 'privmsg', 'new', reply_to=self.message_id)
        elif action == 'reply_to_all':
            return href('portal', 'privmsg', 'new', reply_to_all=self.message_id)
        elif action == 'forward':
            return href('portal', 'privmsg', 'new', forward=self.message_id)

    @classmethod
    @transaction.atomic
    def delete_list(cls, user_id, ids):
        if not ids:
            return

        messages = PrivateMessageEntry.objects.only('id', 'read', 'folder') \
                                      .filter(id__in=ids, user__id=user_id)

        trash = PRIVMSG_FOLDERS['trash'][0]
        for message in messages:
            message.folder = None if message.folder == trash else trash
            message.read = True if message.folder == trash else message.read
            message.save()

    def delete(self):
        if self.folder == PRIVMSG_FOLDERS['trash'][0]:
            self.folder = None
        else:
            self.folder = PRIVMSG_FOLDERS['trash'][0]
        self.save()
        return True

    def archive(self):
        if self.folder != PRIVMSG_FOLDERS['archive'][0]:
            self.folder = PRIVMSG_FOLDERS['archive'][0]
            self.save()
            return True
        return False

    def restore(self):
        if self.folder != PRIVMSG_FOLDERS['trash'][0]:
            return False
        f = self.user == self.message.author and 'sent' or 'inbox'
        self.folder = PRIVMSG_FOLDERS[f][0]
        self.save()
        return True

    class Meta:
        order_with_respect_to = 'message'


class StaticPage(models.Model):
    """
    Stores static pages (imprint, license, etc.)
    """
    key = models.SlugField(gettext_lazy('Key'),
        max_length=25, primary_key=True,
        unique=True, db_index=True,
        help_text=gettext_lazy('Will be used to generate the URL. '
                                'Cannot be changed later.'))
    title = models.CharField(gettext_lazy('Title'), max_length=200)
    content = InyokaMarkupField(
        verbose_name=gettext_lazy('Content'),
        help_text=gettext_lazy('Inyoka syntax required.'),
        application='portal',
    )

    class Meta:
        verbose_name = gettext_lazy('Static page')
        verbose_name_plural = gettext_lazy('Static pages')

    def __repr__(self):
        return '<%s:%s "%s">' % (
            self.__class__.__name__,
            self.key,
            self.title,
        )

    def __str__(self):
        return self.title

    def get_absolute_url(self, action='show'):
        return href(*{
            'show': ('portal', self.key),
            'edit': ('portal', self.key, 'edit'),
            'delete': ('portal', self.key, 'delete'),
        }[action])


class StaticFile(models.Model):
    identifier = models.CharField(gettext_lazy('Identifier'),
        max_length=100, unique=True, db_index=True)
    file = models.FileField(gettext_lazy('File'), upload_to='portal/files')
    is_ikhaya_icon = models.BooleanField(
        gettext_lazy('Is Ikhaya icon'),
        default=False,
        help_text=gettext_lazy('Choose this if the file should appear '
                                'as a article or category icon possibility'))

    class Meta:
        verbose_name = gettext_lazy('Static file')
        verbose_name_plural = gettext_lazy('Static files')

    def __str__(self):
        return self.identifier

    def delete(self):
        self.file.delete(save=False)
        super().delete()

    def get_absolute_url(self, action='show'):
        if action == 'show':
            return self.file.url
        return href(*{
            'edit': ('portal', 'files', self.identifier, 'edit'),
            'delete': ('portal', 'files', self.identifier, 'delete')
        }[action])


class Subscription(models.Model):
    objects = SubscriptionManager()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    notified = models.BooleanField(
        gettext_lazy('User was already notified'),
        default=False)
    ubuntu_version = models.CharField(max_length=5, null=True)

    content_type = models.ForeignKey(ContentType, null=True, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField(null=True, db_index=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    @cached_property
    def is_accessible_for_user(self):
        if self.content_type is None:
            return False

        user = self.user
        model = self.content_type.model

        if model == 'topic':
            return user.has_perm('forum.view_forum', self.content_object.forum)
        if model == 'forum':
            return user.has_perm('forum.view_forum', self.content_object)
        if model == 'page':
            return have_wiki_privilege(user, self.content_object.name, 'read')
        if model == 'user':
            return user.has_perm('portal.subscribe_user')
        if model == 'suggestion':
            return user.has_perm('ikhaya.change_event')
        else:
            # inyoka article subscription
            return True

    def can_read(self, forum_id=None):
        if self.content_type is None and not forum_id is None:
            # Check for ubuntu version subscriptions
            from inyoka.forum.models import Forum

            forum = Forum.objects.get(id=forum_id)

            has_perm = self.user.has_perm('forum.view_forum', forum)
            return has_perm

        return self.is_accessible_for_user

    @classmethod
    def create_auto_subscription(cls, user, topic):
        """
        Subscribes a user to the topic if the user has autosubscription enabled.
        Has no effect, if the user has the 'autosubscribe' setting off or is
        subscribed already.

        Parameters
        ----------
        user : User
            The user to subscribe.
        topic : Topic
            The topic to subscribe the user to.

        Returns
        -------
        None.
        """
        subscribed = cls.objects.user_subscribed(user, topic)
        if user.settings.get('autosubscribe', True) and not subscribed:
             cls.objects.create(user=user, content_object=topic)


class LinkmapManager(models.Manager):

    def flush_cache(self):
        """
        Removes all cache entries for the Linkmap model.
        This should be called, if entries of Linkmap were edited.
        """
        cache.delete_many((Linkmap.CACHE_KEY_MAP, Linkmap.CACHE_KEY_CSS))

    def get_linkmap(self):
        """
        Return a token-to-url-mapping as dictionary for our interwiki links.
        """

        def callback():
            return dict(self.get_queryset().values_list('token', 'url'))

        return cache.get_or_set(Linkmap.CACHE_KEY_MAP, callback, timeout=None)

    def get_css_basename(self):
        """
        Returns the current basename (which includes a changing hash) of the
        current linkmap css. It will also trigger the creation of the css on
        startup or after a change to the linkmap (as the cache key should be
        deleted).

        This method is mainly intended the be used for the template context.
        """
        return cache.get_or_set(Linkmap.CACHE_KEY_CSS, self.generate_css, timeout=None)

    def generate_css(self):
        """
        Generates for each token with icon in Linkmap a piece of css. Latter will
        display the icon near an interwiki link.

        The css is saved at `settings.INYOKA_INTERWIKI_CSS_PATH`. Furthermore, a
        gzip-compressed version with the same content will be saved at the same
        place with a '.gz' postfix.

        A md5-hashsum is used to ensure that browser caches are flushed, if the
        content of the file changed.

        Returns the basename of the current css file.
        """
        css = '/* linkmap for inter wiki links \n :license: BSD*/'

        token_with_icons = self.get_queryset().exclude(icon='').only('token', 'icon')
        for token in token_with_icons:
            css += 'a.interwiki-{token} {{' \
                   'padding-left: 20px; ' \
                   'background-image: url("{icon_url}"); }}'.format(token=token.token,
                                                                    icon_url=token.icon.url)

        md5_css = hashlib.md5(css.encode()).hexdigest()
        path = settings.INYOKA_INTERWIKI_CSS_PATH.format(hash=md5_css)

        existing_files = glob.glob(settings.INYOKA_INTERWIKI_CSS_PATH.format(hash='*'))
        if path in existing_files:
            return os.path.basename(path)

        directory = os.path.dirname(path)
        if not os.path.exists(directory):
            os.makedirs(directory)

        with open(path, 'w') as f, gzip.open(path + '.gz', 'wt') as compressed:
            f.write(css)
            compressed.write(css)

        for f in existing_files:
            os.remove(f)
            os.remove(f + '.gz')

        return os.path.basename(path)


class Linkmap(models.Model):
    """
    Provides an mapping for the interwikilinks from token to urls.
    """
    CACHE_KEY_MAP = 'portal:linkmap'
    CACHE_KEY_CSS = 'portal:linkmap:css-filname'

    token_validator = RegexValidator(regex=r'^[a-z\-_]+[1-9]*$',
                                     message=gettext_lazy('Only lowercase letters, - and _ allowed. Numbers as postfix.'))

    token = models.CharField(gettext_lazy('Token'), max_length=128, unique=True,
                             validators=[token_validator])
    url = models.URLField(gettext_lazy('Link'))
    icon = models.ImageField(gettext_lazy('Icon'), upload_to='linkmap/icons', blank=True)

    objects = LinkmapManager()


class Storage(models.Model):
    key = models.CharField(max_length=200, db_index=True)
    value = InyokaMarkupField(application='portal')
