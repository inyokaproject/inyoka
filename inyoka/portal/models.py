# -*- coding: utf-8 -*-
"""
    inyoka.portal.models
    ~~~~~~~~~~~~~~~~~~~~

    Models for the portal.

    :copyright: (c) 2007-2016 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType, ContentTypeManager
from django.core.cache import cache
from django.db import models, transaction
from django.utils.translation import ugettext_lazy
from werkzeug import cached_property

from inyoka.forum.acl import have_privilege as have_forum_privilege
from inyoka.portal.user import User
from inyoka.utils.database import InyokaMarkupField
from inyoka.utils.text import slugify
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
    content = InyokaMarkupField(
        verbose_name=ugettext_lazy(u'Content'),
        help_text=ugettext_lazy(u'Inyoka syntax required.'),
        application='portal',
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
    content_object = GenericForeignKey('content_type', 'object_id')

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


class Storage(models.Model):
    key = models.CharField(max_length=200, db_index=True)
    value = InyokaMarkupField(application='portal')
