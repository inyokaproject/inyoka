# -*- coding: utf-8 -*-
"""
    inyoka.portal.models
    ~~~~~~~~~~~~~~~~~~~~

    Models for the portal.

    :copyright: (c) 2007-2013 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from werkzeug import cached_property

from django.contrib.contenttypes import models as gmodels
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.db import models, transaction
from django.utils.translation import ugettext_lazy

from inyoka.forum.acl import have_privilege as have_forum_privilege
from inyoka.markup import parse, render, RenderContext
from inyoka.portal.user import User
from inyoka.utils.local import current_request
from inyoka.utils.text import slugify
from inyoka.utils.urls import href
from inyoka.wiki.acl import has_privilege as have_wiki_privilege


class SubscriptionManager(gmodels.ContentTypeManager):
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

        subscribed = Subscription.objects.filter(**filter).exists()
        if clear_notified and subscribed:
            Subscription.objects.filter(**filter).update(notified=False)
        return subscribed

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


class SessionInfo(models.Model):
    """
    A special class that holds session information.  Not every session
    automatically has a session info.  Basically every user that is
    active has a session info that is updated every request.  The
    management functions for this model are in `inyoka.utils.sessions`.
    """
    key = models.CharField(max_length=200, unique=True, db_index=True)
    last_change = models.DateTimeField(db_index=True)
    subject_text = models.CharField(max_length=100, null=True)
    subject_type = models.CharField(max_length=20)
    subject_link = models.CharField(max_length=200, null=True)
    action = models.CharField(max_length=500)
    action_link = models.CharField(max_length=200, null=True)
    category = models.CharField(max_length=200, null=True)


PRIVMSG_FOLDERS_DATA = (
    (0, 'sent', ugettext_lazy(u'Send')),
    (1, 'inbox', ugettext_lazy(u'Inbox')),
    (2, 'trash', ugettext_lazy(u'Trash')),
    (3, 'archive', ugettext_lazy(u'Archive')))


PRIVMSG_FOLDERS = {}
for folder in PRIVMSG_FOLDERS_DATA:
    PRIVMSG_FOLDERS[folder[0]] = PRIVMSG_FOLDERS[folder[1]] = folder


class PrivateMessage(models.Model):
    """
    Private messages allow users to communicate with each other privately.
    This model represent one of these messages.
    """
    author = models.ForeignKey(User)
    subject = models.CharField(ugettext_lazy(u'Title'), max_length=255)
    pub_date = models.DateTimeField(ugettext_lazy(u'Date'))
    text = models.TextField(ugettext_lazy(u'Text'))

    class Meta:
        ordering = ('-pub_date',)

    def send(self, recipients):
        self.save()
        PrivateMessageEntry(message=self, user=self.author, read=True,
                            folder=PRIVMSG_FOLDERS['sent'][0]).save()
        for recipient in recipients:
            cache.delete('portal/pm_count/%s' % recipient.id)
            PrivateMessageEntry(message=self, user=recipient, read=False,
                                folder=PRIVMSG_FOLDERS['inbox'][0]).save()

    @property
    def recipients(self):
        if not hasattr(self, '_recipients'):
            entries = PrivateMessageEntry.objects.filter(message=self) \
                .exclude(user=self.author)
            self._recipients = [e.user for e in entries]
        return self._recipients

    @property
    def author_avatar(self):
        return self.author.get_profile()

    @property
    def rendered_text(self):
        context = RenderContext(current_request)
        return parse(self.text).render(context, 'html')

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
    message = models.ForeignKey('PrivateMessage')
    user = models.ForeignKey(User)
    read = models.BooleanField(ugettext_lazy(u'Read'))
    folder = models.SmallIntegerField(ugettext_lazy(u'Folder'),
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
    @transaction.commit_manually
    def delete_list(cls, user_id, ids):
        if not ids:
            return

        messages = PrivateMessageEntry.objects.only('id', 'read', 'folder') \
                                      .filter(id__in=ids, user__id=user_id)

        trash = PRIVMSG_FOLDERS['trash'][0]
        for message in messages:
            message.folder = None if message.folder == trash else trash
            message.read = True if folder == trash else message.read
            message.save()
        transaction.commit()

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
    key = models.SlugField(ugettext_lazy(u'Key'),
        max_length=25, primary_key=True,
        unique=True, db_index=True,
        help_text=ugettext_lazy(u'Will be used to generate the URL. '
                                u'Cannot be changed later.'))
    title = models.CharField(ugettext_lazy(u'Title'), max_length=200)
    content = models.TextField(ugettext_lazy(u'Content'),
        help_text=ugettext_lazy(u'Inyoka syntax required.')
    )

    class Meta:
        verbose_name = ugettext_lazy(u'Static page')
        verbose_name_plural = ugettext_lazy(u'Static pages')

    def __repr__(self):
        return '<%s:%s "%s">' % (
                self.__class__.__name__,
                self.key,
                self.title,
            )

    def __unicode__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = slugify(self.title)
        return super(StaticPage, self).save(*args, **kwargs)

    def get_absolute_url(self, action='show'):
        return href(*{
            'show': ('portal', self.key),
            'edit': ('portal', self.key, 'edit'),
            'delete': ('portal', self.key, 'delete'),
        }[action])

    @property
    def rendered_content(self):
        context = RenderContext(current_request)
        key = '/portal/staticpage/%s' % self.key
        instructions = cache.get(key)
        if instructions is None:
            instructions = parse(self.content).compile('html')
            cache.set(key, instructions)
        return render(instructions, context)


class StaticFile(models.Model):
    identifier = models.CharField(ugettext_lazy('Identifier'),
        max_length=100, unique=True, db_index=True)
    file = models.FileField(ugettext_lazy('File'), upload_to='portal/files')
    is_ikhaya_icon = models.BooleanField(
        ugettext_lazy(u'Is Ikhaya icon'),
        default=False,
        help_text=ugettext_lazy(u'Choose this if the file should appear '
                                u'as a article or category icon possibility'))

    class Meta:
        verbose_name = ugettext_lazy('Static file')
        verbose_name_plural = ugettext_lazy(u'Static files')

    def __unicode__(self):
        return self.identifier

    def delete(self):
        self.file.delete(save=False)
        super(StaticFile, self).delete()

    def get_absolute_url(self, action='show'):
        if action == 'show':
            return self.file.url
        return href(*{
            'edit': ('portal', 'files', self.identifier, 'edit'),
            'delete': ('portal', 'files', self.identifier, 'delete')
        }[action])


class Subscription(models.Model):
    objects = SubscriptionManager()
    user = models.ForeignKey(User)
    notified = models.BooleanField(
        ugettext_lazy('User was already notified'),
        default=False)
    ubuntu_version = models.CharField(max_length=5, null=True)

    content_type = models.ForeignKey(ContentType, null=True)
    object_id = models.PositiveIntegerField(null=True, db_index=True)
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    @cached_property
    def can_read(self):
        if self.content_type is None:
            # e.g ubuntu version
            return True

        user = self.user
        if self.content_type.model in ('topic', 'forum'):
            return have_forum_privilege(user, self.content_object, 'read')
        elif self.content_type.model == 'page':
            return have_wiki_privilege(user, self.content_object.name, 'read')
        else:
            # e.g user subscriptions
            return True


class SearchQueueManager(models.Manager):
    def append(self, component, doc_id):
        """Append an item to the queue for later indexing."""
        item = self.model()
        item.component = component
        item.doc_id = doc_id
        item.save()

    @transaction.commit_manually
    def multi_insert(self, component, ids):
        for doc_id in ids:
            entry = SearchQueue(component=component, doc_id=doc_id)
            entry.save()
        transaction.commit()


class SearchQueue(models.Model):
    """
    Managing a to-do list for asynchronous indexing.
    """
    objects = SearchQueueManager()
    component = models.CharField(max_length=1)
    doc_id = models.IntegerField()

    class Meta:
        ordering = ['id']


class Storage(models.Model):
    key = models.CharField(max_length=200, db_index=True)
    value = models.TextField()
