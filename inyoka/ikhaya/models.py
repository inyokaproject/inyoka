# -*- coding: utf-8 -*-
"""
    inyoka.ikhaya.models
    ~~~~~~~~~~~~~~~~~~~~

    Database models for ikhaya.

    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from datetime import datetime
from operator import itemgetter, attrgetter

from django.core.cache import cache
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import datetime_safe

from inyoka.portal.user import User
from inyoka.portal.models import StaticFile
from inyoka.wiki.parser import render, parse, RenderContext
from inyoka.utils.text import slugify
from inyoka.utils.html import escape, striptags
from inyoka.utils.urls import href
from inyoka.utils.dates import date_time_to_datetime, datetime_to_timezone, \
     natural_date, format_time, format_datetime
from inyoka.utils.local import current_request
from inyoka.utils.decorators import deferred
from inyoka.utils.database import find_next_increment, LockableObject


def _get_not_cached_articles(keys, cache_values):
    """Return a tuple of (dates, slugs) for all keys in cache_values that are None"""
    not_cached = [(x[1], x[2]) for x in keys if x[0] not in cache_values]
    dates, slugs = map(itemgetter(0), not_cached), map(itemgetter(1), not_cached)
    return dates, slugs


class ArticleManager(models.Manager):

    def __init__(self, public=True, all=False):
        models.Manager.__init__(self)
        self._public = public
        self._all = all

    def get_query_set(self):
        q = super(ArticleManager, self).get_query_set()
        if not self._all:
            q = q.filter(public=self._public)
            if self._public:
                q = q.filter(Q(pub_date__lt=datetime.utcnow().date())|
                             Q(pub_date = datetime.utcnow().date(), pub_time__lte = datetime.utcnow().time()))
            else:
                q = q.filter(Q(pub_date__gt=datetime.utcnow().date())|
                             Q(pub_date = datetime.utcnow().date(), pub_time__gte = datetime.utcnow().time()))
        return q

    def get_cached(self, keys):
        """Get some articles from the cache. `keys` must be a list with
        (pub_date, slug) pairs. Missing entries from the cache are
        automatically fetched from the database. This method should be
        also used for retrieving single objects.

        ATTENTION: All articles which are returned from this function
        don't contain any text or intro (but they will contain rendered_text
        and rendered_intro). So do NEVER save any article returned by
        this function.
        """
        keys = map(lambda x: ('ikhaya/article/%s/%s' % x, x[0], x[1]), keys)
        cache_values = cache.get_many(map(itemgetter(0), keys))
        dates, slugs = _get_not_cached_articles(keys, cache_values)

        objects = Article.objects.filter(slug__in=slugs, pub_date__in=dates) \
                         .select_related('author__username', 'category', 'icon',
                                         'category__icon').order_by()
        new_cache_values = {}
        for article in objects:
            key = 'ikhaya/article/%s/%s' % (article.pub_date, article.slug)
            # render text and intro (and replace the getter to make caching
            # possible)
            article._rendered_text = unicode(article.rendered_text)
            article._rendered_intro = unicode(article.rendered_intro)
            article._simplified_text = unicode(article.simplified_text)
            article._simplified_intro = unicode(article.simplified_intro)
            article.text = article.intro = None
            new_cache_values[key] = article
        if new_cache_values:
            cache.set_many(new_cache_values, 24 * 60) # cache for 24 hours
        cache_values.update(new_cache_values)
        articles = filter(None, cache_values.values())
        unpublished = list(sorted([a for a in articles if not a.public],
                                  key=attrgetter('updated'), reverse=True))
        published = list(sorted([a for a in articles if not a in unpublished],
                                key=attrgetter('updated'), reverse=True))
        return unpublished + published

    def get_latest_articles(self, category=None, count=10):
        key = 'ikhaya/latest_articles'
        if category is not None:
            key = 'ikhaya/latest_articles/%s' % category

        articles = cache.get(key)
        if articles is None:
            articles = Article.published.order_by('-updated') \
                                        .values_list('pub_date', 'slug')
            if category:
                articles.filter(category__slug=category)
            maxcount = max(settings.AVAILABLE_FEED_COUNTS['ikhaya_feed_article'])
            articles = list(articles[:maxcount])
            cache.set(key, articles, 1200)

        return self.get_cached(articles[:count])


class SuggestionManager(models.Manager):

    def delete(self, ids):
        """
        Deletes a list of suggestions with only one query and refresh the caches.
        """
        Suggestion.objects.filter(id__in=ids).delete()
        cache.delete('ikhaya/suggestion_count')


class CommentManager(models.Manager):

    def get_latest_comments(self, article=None, count=10):
        key = 'ikhaya/latest_comments'
        if article is not None:
            key = 'ikhaya/latest_comments/%s' % article

        maxcount = max(settings.AVAILABLE_FEED_COUNTS['ikhaya_feed_comment'])
        comment_ids = cache.get(key)
        if comment_ids is None:
            comment_ids = Comment.objects.filter(article__public=True, deleted=False)
            if article:
                comment_ids = comment_ids.filter(article__id=article)

            comment_ids = list(comment_ids.values_list('id', flat=True)[:maxcount])
            cache.set(key, comment_ids, 300)

        comments = list(Comment.objects.filter(id__in=comment_ids) \
                               .select_related('author__username', 'article__subject') \
                               .order_by('-id')[:maxcount])
        return comments[:count]


class Category(models.Model):
    name = models.CharField(max_length=180)
    slug = models.CharField('Slug', max_length=100, blank=True, unique=True, db_index=True)
    icon = models.ForeignKey(StaticFile, blank=True, null=True,
                             verbose_name='Icon', on_delete=models.SET_NULL)

    def __unicode__(self):
        return self.name

    def get_absolute_url(self, action='show'):
        return href(*{
            'show': ('ikhaya', 'category', self.slug),
            'edit': ('ikhaya', 'category', self.slug, 'edit')
        }[action])

    def save(self, *args, **kwargs):
        # only set the slug on first save.
        if not self.pk:
            self.slug = find_next_increment(Category, 'slug', slugify(self.name))
        super(Category, self).save(*args, **kwargs)
        cache.delete('ikhaya/categories')

    class Meta:
        verbose_name = 'Kategorie'
        verbose_name_plural = 'Kategorien'


class Article(models.Model, LockableObject):
    lock_key_base = 'ikhaya/article_lock'

    objects = ArticleManager(all=True)
    published = ArticleManager(public=True)
    drafts = ArticleManager(public=False)

    pub_date = models.DateField('Datum', db_index=True)
    pub_time = models.TimeField('Zeit')
    updated = models.DateTimeField('Letzte Änderung', blank=True, null=True, 
                                   db_index=True)
    author = models.ForeignKey(User, related_name='article_set',
                               verbose_name='Autor')
    subject = models.CharField('Überschrift', max_length=180)
    category = models.ForeignKey(Category, verbose_name='Kategorie',
                                 on_delete=models.PROTECT)
    icon = models.ForeignKey(StaticFile, blank=True, null=True,
                             verbose_name='Icon', on_delete=models.SET_NULL)
    intro = models.TextField('Einleitung')
    text = models.TextField('Text')
    public = models.BooleanField('Veröffentlicht')
    slug = models.SlugField('Slug', max_length=100, blank=True, db_index=True)
    is_xhtml = models.BooleanField('XHTML Markup', default=False)
    comment_count = models.IntegerField(default=0)
    comments_enabled = models.BooleanField('Kommentare erlaubt', default=True)

    @property
    def article_icon(self):
        return self.icon or self.category.icon

    @deferred
    def pub_datetime(self):
        return date_time_to_datetime(self.pub_date, self.pub_time)

    @property
    def local_pub_datetime(self):
        return datetime_to_timezone(self.pub_datetime).replace(tzinfo=None)

    @property
    def local_updated(self):
        return datetime_to_timezone(self.updated).replace(tzinfo=None)

    def _simplify(self, text, key):
        """Remove markup of a text that belongs to this Article"""
        if self.is_xhtml:
            simple = striptags(text)
        else:
            simple = parse(text).text
        return simple.strip()

    def _render(self, text, key):
        """Render a text that belongs to this Article to HTML"""
        if self.is_xhtml:
            return text
        context = RenderContext(current_request, application='ikhaya')
        instructions = parse(text).compile('html')
        return render(instructions, context)

    @property
    def rendered_text(self):
        if not hasattr(self, '_rendered_text'):
            self._rendered_text = self._render(self.text, 'ikhaya/article_text/%s' % self.id)
        return self._rendered_text

    @property
    def rendered_intro(self):
        if not hasattr(self, '_rendered_intro'):
            self._rendered_intro = self._render(self.intro, 'ikhaya/article_intro/%s' % self.id)
        return self._rendered_intro

    @property
    def simplified_text(self):
        if not hasattr(self, '_simplified_text'):
            self._simplified_text = self._simplify(self.text, 'ikhaya/simple_text/%s' % self.id)
        return self._simplified_text

    @property
    def simplified_intro(self):
        if not hasattr(self, '_simplified_intro'):
            self._simplified_intro = self._simplify(self.intro, 'ikhaya/simple_intro/%s' % self.id)
        return self._simplified_intro

    @property
    def hidden(self):
        """
        This returns a boolean whether this article is not visible for normal
        users.
        Article that are not published or whose pub_date is in the future
        aren't shown for a normal user.
        """
        return not self.public or self.pub_datetime > datetime.utcnow()

    @property
    def comments(self):
        """This returns all the comments for this article"""
        return Comment.objects.filter(article=self)

    @property
    def stamp(self):
        """Return the year/month/day part of an article url"""
        return datetime_safe.new_date(self.pub_date).strftime('%Y/%m/%d')

    def get_absolute_url(self, action='show'):
        if action == 'comments':
            return href('ikhaya', self.stamp, self.slug, _anchor='comments')
        if action in ('subscribe', 'unsubscribe'):
            if current_request:
                current = current_request.build_absolute_uri()
                if not self.get_absolute_url() in current:
                    # We may be at the ikhaya index page.
                    return href('ikhaya', self.stamp, self.slug, action,
                                next=current_request.build_absolute_uri())
            return href('ikhaya', self.stamp, self.slug, action)

        links = {
            'delete':     ('ikhaya', self.stamp, self.slug, 'delete'),
            'edit':       ('ikhaya', self.stamp, self.slug, 'edit'),
            'id':         ('portal', 'ikhaya',  self.id),
            'report_new': ('ikhaya', self.stamp, self.slug, 'new_report'),
            'reports':    ('ikhaya', self.stamp, self.slug, 'reports'),
            'show':       ('ikhaya', self.stamp, self.slug),
        }

        return href(*links[action if action in links.keys() else 'show'])

    def __unicode__(self):
        return self.subject

    def save(self, *args, **kwargs):
        """
        This increases the edit count by 1 and updates the xapian database.
        """
        if self.text is None or self.intro is None:
            # might happen, because cached objects are setting text and
            # intro to None to save some space
            raise ValueError(u'text and intro must not be null')
        suffix_id = False

        # We need a local pubdt variable due to caching of self.pub_datetime
        pubdt = date_time_to_datetime(self.pub_date, self.pub_time)
        if not self.updated or self.updated < pubdt:
            self.updated = pubdt

        if not self.slug:
            self.slug = find_next_increment(Article, 'slug',
                slugify(self.subject), pub_date=self.pub_date)

        # Force to use a valid slug
        self.slug = slugify(self.slug)

        super(Article, self).save(*args, **kwargs)

        # now that we have the article id we can put it into the slug
        if suffix_id:
            self.slug = '%s-%s' % (self.slug, self.id)
            Article.objects.filter(id=self.id).update(slug=self.slug)
        cache.delete('ikhaya/archive')
        cache.delete('ikhaya/article_text/%s' % self.id)
        cache.delete('ikhaya/article_intro/%s' % self.id)
        cache.delete('ikhaya/article/%s' % self.slug)

    def delete(self):
        """
        Delete the xapian document.
        Subscriptions are removed by a Django signal `pre_delete`
        """
        id = self.id
        super(Article, self).delete()
        self.id = id

    class Meta:
        verbose_name = 'Artikel'
        verbose_name_plural = 'Artikel'
        ordering = ['-pub_date', '-pub_time', 'author']
        unique_together = ('pub_date', 'slug')


class Report(models.Model):
    article = models.ForeignKey(Article, null=True)
    text = models.TextField()
    author = models.ForeignKey(User)
    pub_date = models.DateTimeField()
    deleted = models.BooleanField(null=False, default=False)
    solved = models.BooleanField(null=False, default=False)
    rendered_text = models.TextField()

    def __repr__(self):
        subject = self.article.subject if self.article else '?'
        if self.pk is None:
            return '<Report on %r>' % subject
        return '<Report #%d on %r>' % (self.pk, subject)

    def get_absolute_url(self, action='show'):
        if action == 'show':
            return href('ikhaya', self.article.stamp, self.article.slug, 'reports')
        return href('ikhaya', 'report', self.id, action)

    def save(self, *args, **kwargs):
        context = RenderContext(current_request)
        node = parse(self.text, wiki_force_existing=False)
        self.rendered_text = node.render(context, 'html')
        super(Report, self).save(*args, **kwargs)
        if self.id:
            cache.delete('ikhaya/report/%d' % self.id)


class Suggestion(models.Model):
    objects = SuggestionManager()
    author = models.ForeignKey(User, related_name='suggestion_set')
    pub_date = models.DateTimeField('Datum', default=datetime.utcnow)
    title = models.CharField(u'Titel', max_length=100)
    text = models.TextField(u'Text')
    intro = models.TextField(u'Einleitung')
    notes = models.TextField(u'Anmerkungen', blank=True, default=u'')
    owner = models.ForeignKey(User, related_name='owned_suggestion_set',
                              null=True, blank=True)

    class Meta:
        verbose_name = 'Artikelvorschlag'
        verbose_name_plural = 'Artikelvorschläge'

    @property
    def rendered_text(self):
        context = RenderContext(current_request)
        key = 'ikhaya/suggestion_text/%s' % self.id
        instructions = cache.get(key)
        if instructions is None:
            instructions = parse(self.text).compile('html')
            cache.set(key, instructions)
        return render(instructions, context)

    @property
    def rendered_intro(self):
        context = RenderContext(current_request)
        key = 'ikhaya/suggestion_intro/%s' % self.id
        instructions = cache.get(key)
        if instructions is None:
            instructions = parse(self.intro).compile('html')
            cache.set(key, instructions)
        return render(instructions, context)

    @property
    def rendered_notes(self):
        context = RenderContext(current_request)
        key = 'ikhaya/suggestion_notes/%s' % self.id
        instructions = cache.get(key)
        if instructions is None:
            instructions = parse(self.notes).compile('html')
            cache.set(key, instructions)
        return render(instructions, context)

    def get_absolute_url(self):
        return href('ikhaya', 'suggestions', anchor=self.id)


class Comment(models.Model):
    objects = CommentManager()
    article = models.ForeignKey(Article, null=True)
    text = models.TextField()
    author = models.ForeignKey(User)
    pub_date = models.DateTimeField()
    deleted = models.BooleanField(null=False, default=False)
    rendered_text = models.TextField()

    def get_absolute_url(self, action='show'):
        if action in ['hide', 'restore', 'edit']:
            return href('ikhaya', 'comment', self.id, action)
        return href('ikhaya', self.article.stamp, self.article.slug,
                    _anchor='comment_%s' % self.article.comment_count)

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.article = Article.objects.get(id=self.article.id)
            self.article.comment_count = self.article.comment_count + 1
            self.article.save()
        context = RenderContext(current_request)
        node = parse(self.text, wiki_force_existing=False)
        self.rendered_text = node.render(context, 'html')
        super(Comment, self).save(*args, **kwargs)
        if self.id:
            cache.delete('ikhaya/comment/%d' % self.id)


class Event(models.Model):
    class Meta:
        db_table = 'portal_event'
        app_label = 'portal'

    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True, max_length=100, db_index=True)
    changed = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    date = models.DateField(db_index=True)
    time = models.TimeField(blank=True, null=True) # None -> whole day
    enddate = models.DateField(blank=True, null=True) # None
    endtime = models.TimeField(blank=True, null=True) # None -> whole day
    description = models.TextField(blank=True)
    author = models.ForeignKey(User)
    location = models.CharField(max_length=128, blank=True)
    location_town = models.CharField(max_length=56, blank=True)
    location_lat = models.FloatField(u'Koordinaten (Breite)',
                                     blank=True, null=True)
    location_long = models.FloatField('Koordinaten (Länge)',
                                      blank=True, null=True)
    visible = models.BooleanField(default=False)

    def get_absolute_url(self, action='show'):
        if action == 'copy':
            return href('ikhaya', 'event', 'new', copy_from=self.id)
        return href(*{
            'show':   ('portal', 'calendar', self.slug),
            'delete': ('ikhaya', 'event', self.id, 'delete'),
            'edit':   ('ikhaya', 'event', self.id, 'edit'),
            'new':    ('ikhaya', 'event', 'new'),
        }[action])

    @property
    def rendered_description(self):
        context = RenderContext(current_request)
        key = 'ikhaya/date/%s' % self.id
        instructions = cache.get(key)
        if instructions is None:
            instructions = parse(self.description).compile('html')
            cache.set(key, instructions)
        return render(instructions, context)

    def save(self, *args, **kwargs):
        if not self.slug:
            name = datetime_safe.new_date(self.date) \
                                .strftime('%Y/%m/%d/') + slugify(self.name)
            self.slug = find_next_increment(Event, 'slug', name, stripdate=True)
        super(self.__class__, self).save(*args, **kwargs)
        cache.delete('ikhaya/event/%s' % self.id)
        cache.delete('ikhaya/event_count')

    def friendly_title(self, with_date=True, with_html_link=False):
        if with_date:
            s_date = self.natural_datetime
        else:
            s_date = ''
        s_location = '<span class="location">%s</span>' % (
             self.location_town and u' in %s' % self.location_town or '')
        summary = u'<span class="summary">%s</span>' % escape(self.name)
        if with_html_link:
            ret = u'<a href="%s" class="event_link">%s</a>%s%s' % (
                escape(self.get_absolute_url()),
                summary,
                s_date,
                s_location)
        else:
            ret = summary + s_date + s_location
        return u'<span class="vevent">%s</span>' % ret

    @property
    def natural_datetime(self):
        def _convert(d, t=None, time_only=False, prefix=True, end=False):
            if t is None:
                return natural_date(d, prefix)
            class_ = 'dtend' if end else 'dtstart'
            format_ = format_time if time_only else format_datetime
            dt = date_time_to_datetime(d, t)
            return '<abbr title="%s" class="%s">%s</abbr>' % (dt.isoformat(),
                  class_, format_(dt))

        """
        SD  ST  ED  ET
        x   -   -   -   am dd.mm.yyyy
        x   -   x   -   vom dd.mm.yyyy bis dd.mm.yyyy
        x   -   -   x   am dd.mm.yyyy                               ignore the ET
        x   -   x   x   vom dd.mm.yyyy bis dd.mm.yyyy               ignore the ET
        x   x   -   -   dd.mm.yyyy HH:MM
        x   x   x   -   dd.mm.yyyy HH:MM bis dd.mm.yyyy HH:MM       set ET to ST by convention
        x   x   -   x   dd.mm.yyyy HH:MM bis HH:MM
        x   x   x   x   dd.mm.yyyy HH:MM bis dd.mm.yyyy HH:MM
        """

        if self.time is None:
            if self.enddate is None or self.enddate <= self.date:
                return ' ' + _convert(self.date)
            else:
                prefix = ' von ' if -1 <= (self.enddate - self.date).days <= 1 else ' vom '
                return prefix + _convert(self.date, None, False, False) + ' bis ' + _convert(self.enddate, None, False, False, True)
        else:
            if self.enddate is None and self.endtime is None:
                return ' ' + _convert(self.date, self.time)
            else:
                """
                since, one endpoint information is given, we calculate the duration:
                if no enddate is set, we take the startdate as enddate, too
                if no endtime is set, we take the starttime as endtime, too
                """
                #self.enddate = self.enddate or self.date
                self.endtime = self.endtime or self.time
                start = date_time_to_datetime(self.date, self.time)
                end = date_time_to_datetime(self.enddate or self.date, self.endtime)
                if end > start:
                    delta = end - start
                else:
                    # return the same as if no endpoint is given
                    return " " + _convert(self.date, self.time)

                if not delta.days:
                    # duration < 1 day
                    return " am " + _convert(self.date, self.time, False) + ' bis ' + _convert(self.date, self.endtime, True, False, True)
                else:
                    return " " + _convert(self.date, self.time, False, False) + ' bis ' + _convert(self.enddate, self.endtime, False, False, True)

    @property
    def natural_coordinates(self):
        if self.location_lat and self.location_long:
            lat = self.location_lat > 0 and u'%g° N' % self.location_lat \
                                        or u'%g° S' % -self.location_lat
            long = self.location_long > 0 and u'%g° O' % self.location_long\
                                          or u'%g° W' % -self.location_long
            return u'%s, %s' % (lat, long)
        else:
            return u''

    @property
    def simple_coordinates(self):
        return u'%s;%s' % (self.location_lat, self.location_long)

    @property
    def coordinates_url(self):
        lat = self.location_lat > 0 and '%g_N' % self.location_lat \
                                    or '%g_S' % -self.location_lat
        long = self.location_long > 0 and '%g_E' % self.location_long\
                                      or '%g_W' % -self.location_long
        return 'http://tools.wikimedia.de/~magnus/geo/geohack.php?language' \
               '=de&params=%s_%s' % (lat, long)


#: Register generic model signals
from inyoka.utils import signals
