# -*- coding: utf-8 -*-
"""
    inyoka.pastebin.models
    ~~~~~~~~~~~~~~~~~~~~~~

    Database models for the pastebin.

    :copyright: (c) 2007-2013 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from datetime import datetime
from urlparse import urlparse

from django.db import models
from django.utils.translation import ugettext_lazy

from inyoka.portal.user import User
from inyoka.utils.highlight import highlight_code
from inyoka.utils.urls import href, is_safe_domain


class Entry(models.Model):
    title = models.CharField(ugettext_lazy('Title'), max_length=40)
    lang = models.CharField(ugettext_lazy('Language'), max_length=20)
    code = models.TextField(ugettext_lazy('Code'))
    rendered_code = models.TextField(ugettext_lazy('Rendered code'))
    pub_date = models.DateTimeField(ugettext_lazy('Date'), db_index=True,
                                    default=datetime.utcnow)
    author = models.ForeignKey(User, verbose_name=ugettext_lazy('Author'),
                               on_delete=models.PROTECT)
    referrer = models.TextField(ugettext_lazy('Referencing pages'), blank=True)

    class Meta:
        verbose_name = ugettext_lazy('Entry')
        verbose_name_plural = ugettext_lazy('Entries')
        ordering = ('-id',)

    @property
    def referrer_list(self):
        return [x for x in self.referrer.splitlines() if x]

    def add_referrer(self, referrer):
        if is_safe_domain(referrer):
            # make sure that the referrer isn't a pastebin url
            netloc = urlparse(referrer)[1]
            if ('.' + netloc).endswith(('.' + urlparse(href('pastebin'))[1])):
                return False
            if '?' in referrer:
                referrer = referrer.split('?')[0]
            r = self.referrer_list
            if referrer in r:
                return False
            r.append(referrer)
            self.referrer = u'\n'.join(sorted(r))
            return True
        return False

    def get_absolute_url(self, action='show'):
        return href(*{
            'show': ('pastebin', self.id),
            'raw': ('pastebin', 'raw', self.id),
            'delete': ('pastebin', 'delete', self.id)
        }[action])

    def save(self, *args, **kwargs):
        self.rendered_code = highlight_code(self.code, self.lang)
        super(Entry, self).save(*args, **kwargs)
