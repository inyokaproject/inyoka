"""
    inyoka.pastebin.models
    ~~~~~~~~~~~~~~~~~~~~~~

    Database models for the pastebin.

    :copyright: (c) 2007-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.db import models
from django.utils import timezone as dj_timezone
from django.utils.translation import gettext_lazy

from inyoka.portal.user import User
from inyoka.utils.database import PygmentsField
from inyoka.utils.urls import href


class Entry(models.Model):
    title = models.CharField(gettext_lazy('Title'), max_length=40)
    lang = models.CharField(gettext_lazy('Language'), max_length=20)
    code = PygmentsField(application='pastebin')
    pub_date = models.DateTimeField(gettext_lazy('Date'), db_index=True,
                                    default=dj_timezone.now)
    author = models.ForeignKey(User, verbose_name=gettext_lazy('Author'), on_delete=models.CASCADE)

    class Meta:
        verbose_name = gettext_lazy('Entry')
        verbose_name_plural = gettext_lazy('Entries')
        ordering = ('-id',)

    def get_absolute_url(self, action='show'):
        return href(*{
            'show': ('pastebin', self.id),
            'raw': ('pastebin', 'raw', self.id),
            'delete': ('pastebin', 'delete', self.id)
        }[action])
