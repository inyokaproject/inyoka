# -*- coding: utf-8 -*-
"""
    inyoka.planet.models
    ~~~~~~~~~~~~~~~~~~~~

    Database models for the planet.

    :copyright: (c) 2007-2012 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from django.core.cache import cache
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy, ugettext as _

from inyoka.utils.urls import href, url_for
from inyoka.utils.search import search, SearchAdapter
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
    name = models.CharField(ugettext_lazy(u'Name of the blog'), max_length=40)
    description = models.TextField(ugettext_lazy(u'Description'), blank=True, null=True)
    blog_url = models.URLField(ugettext_lazy(u'URL of the blog'), verify_exists=False)
    feed_url = models.URLField(ugettext_lazy(u'URL of the feed'), verify_exists=False)
    user = models.ForeignKey(User, verbose_name=ugettext_lazy(u'User'),
                             blank=True, null=True)
    icon = models.ImageField(ugettext_lazy(u'Icon'), upload_to='planet/icons', blank=True)
    last_sync = models.DateTimeField(blank=True, null=True)
    active = models.BooleanField(ugettext_lazy(u'Index the blog'), default=True)

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

    def update_search(self):
        """
        This updates the xapian search index.
        """
        PlanetSearchAdapter.queue(self.id)

    def save(self, *args, **kwargs):
        super(Entry, self).save(*args, **kwargs)
        blog = self.blog
        if (not blog.last_sync or self.updated > blog.last_sync) and blog.active:
            self.update_search()

    def delete(self):
        super(Entry, self).delete()
        # update search
        self.update_search()

    class Meta:
        verbose_name = ugettext_lazy(u'Entry')
        verbose_name_plural = ugettext_lazy(u'Entries')
        get_latest_by = 'pub_date'
        ordering = ('-pub_date',)


class PlanetSearchAdapter(SearchAdapter):
    type_id = 'p'

    def get_objects(self, docids):
        return Entry.objects.select_related(depth=1) \
                    .filter(id__in=docids).all()

    def extract_data(self, entry):
        return {'title': entry.title,
                'user': entry.blog.name,
                'user_url': entry.blog.blog_url,
                'date': entry.pub_date,
                'url': url_for(entry),
                'component': u'Planet',
                'group': entry.blog.name,
                'group_url': url_for(entry.blog),
                'text': entry.text,
                'hidden': entry.hidden}

    def recv(self, entry_id):
        entry = Entry.objects.select_related(depth=1).get(id=entry_id)
        return self.extract_data(entry)

    def recv_multi(self, entry_ids):
        entries = Entry.objects.select_related(depth=1).filter(id__in=entry_ids)
        return [self.extract_data(entry) for entry in entries]

    def store_object(self, entry, connection=None):
        search.store(connection,
            component='p',
            uid=entry.id,
            title=entry.title,
            text=entry.simplified_text,
            date=entry.pub_date,
            category=entry.blog.name
        )

    def get_doc_ids(self):
        ids = Entry.objects.values_list('id', flat=True)
        for id in ids:
            yield id


search.register(PlanetSearchAdapter())
