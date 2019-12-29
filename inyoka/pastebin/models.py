# -*- coding: utf-8 -*-
"""
    inyoka.pastebin.models
    ~~~~~~~~~~~~~~~~~~~~~~

    Database models for the pastebin.

    :copyright: (c) 2007-2020 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime

from django.db import models
from django.utils.translation import ugettext_lazy

from inyoka.portal.user import User
from inyoka.utils.database import PygmentsField
from inyoka.utils.urls import href


class Entry(models.Model):
    title = models.CharField(ugettext_lazy('Title'), max_length=40)
    lang = models.CharField(ugettext_lazy('Language'), max_length=20)
    code = PygmentsField(application='pastebin')
    pub_date = models.DateTimeField(ugettext_lazy('Date'), db_index=True,
                                    default=datetime.utcnow)
    author = models.ForeignKey(User, verbose_name=ugettext_lazy('Author'))

    class Meta:
        verbose_name = ugettext_lazy('Entry')
        verbose_name_plural = ugettext_lazy('Entries')
        ordering = ('-id',)
        permissions = (
            ('view_entry', 'Can view Entry'),
        )

    def get_absolute_url(self, action='show'):
        return href(*{
            'show': ('pastebin', self.id),
            'raw': ('pastebin', 'raw', self.id),
            'delete': ('pastebin', 'delete', self.id)
        }[action])
