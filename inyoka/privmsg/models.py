# -*- coding: utf-8 -*-
"""
    inyoka.privmsg.models
    ~~~~~~~~~~~~~~~~~~~~~

    Models for private messages between users.

    :copyright: (c) 2007-2016 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
# import locale
from datetime import datetime, timedelta

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models, transaction
from django.db.models import F, Q
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy

from inyoka.portal.user import User
from inyoka.privmsg.notifications import send_privmsg_notification
from inyoka.utils.database import InyokaMarkupField
from inyoka.utils.urls import url_for


class MessageQuerySet(models.QuerySet):
    def include_related(self):
        """
        Reduce the number of queries that hit the database.
        """
        return self.select_related('messagedata', 'recipient') \
                   .prefetch_related('messagedata__author',
                                     'messagedata__original_recipients')

    def for_user(self, user):
        """
        Return messages for user.
        """
        return self.filter(recipient=user)

    def from_user(self, user):
        """
        Return messages the user sent himself.
        """
        return self.filter(messagedata__author=user)

    def archived(self):
        """
        Return archived messages.
        """
        return self.filter(status=Message.MESSAGE_ARCHIVED)

    def inbox(self):
        """
        Return messages in the inbox (i.e. not archived).
        """
        return self.filter(Q(status=Message.MESSAGE_UNREAD) | Q(status=Message.MESSAGE_READ))

    def sent(self):
        """
        Return sent messages.
        """
        return self.filter(status=Message.MESSAGE_SENT)

    def trashed(self):
        """
        Return messages in the trash.
        """
        return self.filter(status=Message.MESSAGE_TRASHED)

    def deleted(self):
        """
        Return a list of messages that are marked as deleted.
        """
        return self.filter(status=Message.MESSAGE_DELETED)

    def read(self):
        """
        Return read messages.
        """
        return self.filter(status=Message.MESSAGE_READ)

    def unread(self):
        """
        Return unread messages.
        """
        return self.filter(status=Message.MESSAGE_UNREAD)

    def to_expunge(self):
        """
        Return list of messages that can be deleted from the database.
        """
        delta = timedelta(days=settings.PRIVATE_MESSAGE_EXPUNGE_DAYS)
        return self.filter(trashed_date__lt=F('trashed_date') - delta).trashed()


class Message(models.Model):
    """
    Hold an entry for every recipient of a private message.
    """
    MESSAGE_ARCHIVED = 'A'
    MESSAGE_DELETED = 'D'
    MESSAGE_READ = 'R'
    MESSAGE_SENT = 'S'
    MESSAGE_TRASHED = 'T'
    MESSAGE_UNREAD = 'U'
    MESSAGE_STATUS_CHOICES = (
        (MESSAGE_ARCHIVED, _(u'Archived')),
        (MESSAGE_DELETED, _(u'Deleted')),
        (MESSAGE_READ, _(u'Read')),
        (MESSAGE_SENT, _(u'Sent')),
        (MESSAGE_TRASHED, _(u'Trashed')),
        (MESSAGE_UNREAD, _(u'Unread')),
    )

    messagedata = models.ForeignKey('MessageData', on_delete=models.CASCADE)
    recipient = models.ForeignKey(User)
    read_date = models.DateTimeField(null=True, blank=True)
    trashed_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=1,
                              choices=MESSAGE_STATUS_CHOICES,
                              default=MESSAGE_UNREAD)

    objects = MessageQuerySet.as_manager()

    class Meta:
        ordering = ['-messagedata__pub_date']

    def get_absolute_url(self, action='show'):
        """
        Return URLs for this message.
        """
        message_actions = ('archive',
                           'delete',
                           'forward',
                           'restore',
                           'reply',
                           'trash')
        if action in message_actions:
            return reverse('privmsg-message-{}'.format(action), args=[self.id])
        elif action == 'reply_to_all':
            return reverse('privmsg-message-reply-all', args=[self.id])
        elif action == 'folder':
            return reverse('privmsg-{}'.format(self.folder))
        else:
            return reverse('privmsg-message', args=[self.id])

    @property
    def is_unread(self):
        """
        Return True, if the message is unread.
        """
        return self.status == self.MESSAGE_UNREAD

    @property
    def is_own_message(self):
        """
        Return whether or not this message was sent by the recipient.
        """
        return self.recipient == self.author

    @property
    def author(self):
        """
        Return the author of the message. This is a proxy.
        """
        return self.messagedata.author

    @property
    def recipients(self):
        """
        Return the list of recipients. This is a proxy.
        """
        return self.messagedata.original_recipients.all()

    @property
    def subject(self):
        """
        Return the subject of the message. This is a proxy.
        """
        return self.messagedata.subject

    @property
    def text(self):
        """
        Return the text of this message. This is a proxy.
        """
        return self.messagedata.text

    @property
    def text_rendered(self):
        """
        Return the rendered text of this message. This is a proxy.
        """
        return self.messagedata.text_rendered

    @property
    def pub_date(self):
        """
        Return the publication date of this message. This is a proxy.
        """
        return self.messagedata.pub_date

    @property
    def folder(self):
        """
        Return the folder identifier.

        Note, the actual names of these folders only appear in the views/templates where
        strings can be translated.
        """
        if self.status == self.MESSAGE_SENT:
            return 'sent'
        elif self.status == self.MESSAGE_ARCHIVED:
            return 'archive'
        elif self.status == self.MESSAGE_TRASHED:
            return 'trash'
        else:
            return 'inbox'

    def mark_read(self):
        """
        Mark the message as read by the user.
        """
        if self.is_unread:
            self.recipient.privmsg_count.decr()
            self.status = self.MESSAGE_READ
            self.read_date = datetime.utcnow()
            self.save()

    def archive(self):
        """
        Mark the message as archived.
        """
        if self.is_unread:
            self.recipient.privmsg_count.decr()
        self.status = self.MESSAGE_ARCHIVED
        self.save()

    def trash(self):
        """
        Mark the message as trashed.
        """
        if self.is_unread:
            self.recipient.privmsg_count.decr()
        self.status = self.MESSAGE_TRASHED
        self.trashed_date = datetime.utcnow()
        self.save()

    def restore(self):
        """
        Move the message back to the inbox.
        """
        if self.status == self.MESSAGE_TRASHED:
            self.trashed_date = None
        if self.is_own_message:
            self.status = self.MESSAGE_SENT
        else:
            self.status = self.MESSAGE_READ
        self.save()


class MessageData(models.Model):
    """
    Hold the metadata for a private message.
    """
    author = models.ForeignKey(User, related_name='authored_messages')
    subject = models.CharField(ugettext_lazy(u'Title'), max_length=255)
    pub_date = models.DateTimeField(ugettext_lazy(u'Date'), auto_now_add=True)
    text = InyokaMarkupField()
    original_recipients = models.ManyToManyField(User, related_name='+')

    @transaction.atomic
    def send(self, recipients=None):
        """
        Send a copy of this message to each recipient.
        """
        self.original_recipients = recipients

        # Create a message object for the author.
        Message.objects.create(messagedata=self,
                               recipient=self.author,
                               status=Message.MESSAGE_SENT)
        # Create message objects for each recipient, set counter and notify recipients.
        for user in recipients:
            message = Message.objects.create(messagedata=self,
                                             recipient=user)
            send_privmsg_notification(recipient=user,
                                      author=self.author,
                                      subject=self.subject,
                                      url=url_for(message),)
            user.privmsg_count.incr()
