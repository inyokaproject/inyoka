# -*- coding: utf-8 -*-
"""
    inyoka.planet.models
    ~~~~~~~~~~~~~~~~~~~~

    Database models for the planet.

    :copyright: (c) 2007-2021 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.conf import settings
from django.core.cache import cache
from django.db import models
from django.utils.translation import ugettext_lazy

from inyoka.portal.user import User
from inyoka.utils.html import striptags
from inyoka.utils.urls import href


class EntryManager(models.Manager):

    def get_latest_entries(self, count=10):
        key = 'planet/latest_entries'
        entries = cache.get(key)
        if entries is None:
            maxcount = max(settings.AVAILABLE_FEED_COUNTS['planet_feed'])
            entries = list(Entry.objects.filter(hidden=False)[:maxcount])
            cache.set(key, entries, 300)
        return entries[:count]


class Blog(models.Model):
    name = models.CharField(ugettext_lazy('Name of the blog'), max_length=40)
    description = models.TextField(ugettext_lazy('Description'), blank=True, null=True)
    blog_url = models.URLField(ugettext_lazy('URL of the blog'))
    feed_url = models.URLField(ugettext_lazy('URL of the feed'))
    user = models.ForeignKey(User, verbose_name=ugettext_lazy('User'),
                             blank=True, null=True, on_delete=models.CASCADE)
    icon = models.ImageField(ugettext_lazy('Icon'), upload_to='planet/icons', blank=True)
    last_sync = models.DateTimeField(blank=True, null=True)
    active = models.BooleanField(ugettext_lazy('Index the blog'), default=True)

    @property
    def icon_url(self):
        if self.icon:
            return self.icon.url
        return None

    def delete(self):
        self.icon.delete(save=False)
        super(Blog, self).delete()

    def __str__(self):
        return self.name

    def get_absolute_url(self, action='show'):
        if action == 'show':
            return self.blog_url
        else:
            return href(*{
                'edit': ('planet', 'blog', self.id, 'edit'),
                'delete': ('planet', 'blog', self.id, 'delete')
            }[action])

    class Meta:
        ordering = ('name',)
        verbose_name = 'Blog'
        verbose_name_plural = 'Blogs'
        permissions = (
            ('suggest_blog','Can suggest Blogs'),
        )


class Entry(models.Model):
    objects = EntryManager()
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE)
    guid = models.CharField(max_length=200, unique=True, db_index=True)
    title = models.CharField(max_length=140)
    url = models.URLField()
    text = models.TextField()
    pub_date = models.DateTimeField(db_index=True)
    updated = models.DateTimeField(db_index=True)
    author = models.CharField(max_length=50)
    author_homepage = models.URLField(blank=True, null=True)
    hidden = models.BooleanField(default=False)
    hidden_by = models.ForeignKey(User, blank=True, null=True,
                                  related_name='hidden_planet_posts', on_delete=models.CASCADE)

    def __str__(self):
        return '%s / %s' % (
            self.blog,
            self.title
        )

    @property
    def simplified_text(self):
        return striptags(self.text)

    def get_absolute_url(self, action='show'):
        if action == 'show':
            return self.url
        else:
            return href(*{
                'hide': ('planet', 'hide', self.id),
            }[action])

    def save(self, *args, **kwargs):
        super(Entry, self).save(*args, **kwargs)
        blog = self.blog

    def delete(self):
        super(Entry, self).delete()

    class Meta:
        verbose_name = ugettext_lazy('Entry')
        verbose_name_plural = ugettext_lazy('Entries')
        get_latest_by = 'pub_date'
        ordering = ('-pub_date',)
        permissions = (
            ('hide_entry', 'Can hide Entry'),
        )
