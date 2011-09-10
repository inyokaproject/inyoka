# -*- coding: utf-8 -*-
"""
    inyoka.planet.models
    ~~~~~~~~~~~~~~~~~~~~

    Database models for the planet.

    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from django.core.cache import cache
from django.conf import settings
from django.db import models

from inyoka.utils.urls import href
from inyoka.utils.html import striptags
from inyoka.portal.user import User


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
    name = models.CharField(u'Name des Blogs', max_length=40)
    description = models.TextField(u'Beschreibung', blank=True, null=True)
    blog_url = models.URLField(u'URL des Blogs', verify_exists=False)
    feed_url = models.URLField(u'URL des Feeds', verify_exists=False)
    user = models.ForeignKey(User, verbose_name=u'Benutzer',
                             blank=True, null=True)
    icon = models.ImageField(u'Icon', upload_to='planet/icons', blank=True)
    last_sync = models.DateTimeField(blank=True, null=True)
    active = models.BooleanField(u'Blog indizieren', default=True)

    @property
    def icon_url(self):
        if not self.icon:
            return href('static', 'img', 'planet', 'anonymous.png')
        return self.icon.url

    def delete(self):
        self.icon.delete(save=False)
        super(Blog, self).delete()

    def __unicode__(self):
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


class Entry(models.Model):
    objects = EntryManager()
    blog = models.ForeignKey(Blog)
    guid = models.CharField(max_length=200, unique=True, db_index=True)
    title = models.CharField(max_length=140)
    url = models.URLField()
    text = models.TextField()
    pub_date = models.DateTimeField(db_index=True)
    updated = models.DateTimeField(db_index=True)
    author = models.CharField(max_length=50)
    author_homepage = models.URLField(blank=True, null=True)
    hidden = models.BooleanField()
    hidden_by = models.ForeignKey(User, blank=True, null=True,
                                  related_name='hidden_planet_posts')

    def __unicode__(self):
        return u'%s / %s' % (
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
                'hide':     ('planet', 'hide', self.id),
            }[action])

    class Meta:
        verbose_name = 'Eintrag'
        verbose_name_plural = u'Einträge'
        get_latest_by = 'pub_date'
        ordering = ('-pub_date',)
