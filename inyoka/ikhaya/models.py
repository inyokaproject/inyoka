# -*- coding: utf-8 -*-
"""
    inyoka.ikhaya.models
    ~~~~~~~~~~~~~~~~~~~~

    Database models for ikhaya.

    :copyright: (c) 2007-2012 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from datetime import datetime
from operator import itemgetter, attrgetter

from django.core.cache import cache
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy
from django.utils import datetime_safe
from django.utils.html import escape

from inyoka.markup import render, parse, RenderContext
from inyoka.portal.user import User
from inyoka.portal.models import StaticFile

from inyoka.utils.dates import date_time_to_datetime, datetime_to_timezone
from inyoka.utils.database import find_next_increment, LockableObject
from inyoka.utils.decorators import deferred
from inyoka.utils.html import striptags
from inyoka.utils.local import current_request
from inyoka.utils.search import search, SearchAdapter
from inyoka.utils.text import slugify
from inyoka.utils.urls import href, url_for


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
                q = q.filter(Q(pub_date__lt=datetime.utcnow().date()) |
                             Q(pub_date=datetime.utcnow().date(),
                               pub_time__lte=datetime.utcnow().time()))
            else:
                q = q.filter(Q(pub_date__gt=datetime.utcnow().date()) |
                             Q(pub_date=datetime.utcnow().date(),
                               pub_time__gte=datetime.utcnow().time()))
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

        related = ('author__username', 'category', 'icon', 'category__icon')
        objects = Article.objects.filter(slug__in=slugs, pub_date__in=dates) \
                         .select_related(*related).order_by()
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
            # cache for 24 hours
            cache.set_many(new_cache_values, 24 * 60)
        cache_values.update(new_cache_values)
        articles = filter(None, cache_values.values())
        unpublished = list(sorted([a for a in articles if not a.public],
                                  key=attrgetter('updated'), reverse=True))
        published = list(sorted([a for a in articles if not a in unpublished],
                                key=attrgetter('updated'), reverse=True))
        return unpublished + published

    def get_latest_articles(self, category=None, count=10):
        """Return `count` lastest articles for the category `category` or for
        all categories if None.

        :param category: Takes the slug of the category or None
        :param count: maximum retrieve this many articles. Defaults to 10
        :type category: string or None
        :type count: integer

        """
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

        comments = list(Comment.objects.filter(id__in=comment_ids)
                               .select_related('author__username', 'article__subject')
                               .order_by('-id')[:maxcount])
        return comments[:count]


class Category(models.Model):
    name = models.CharField(max_length=180)
    slug = models.CharField(ugettext_lazy(u'Slug'), max_length=100,
            blank=True, unique=True, db_index=True)
    icon = models.ForeignKey(StaticFile, blank=True, null=True,
                             verbose_name=ugettext_lazy(u'Icon'), on_delete=models.SET_NULL)

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
        verbose_name = ugettext_lazy(u'Category')
        verbose_name_plural = ugettext_lazy(u'Categories')


class Article(models.Model, LockableObject):
    lock_key_base = 'ikhaya/article_lock'

    objects = ArticleManager(all=True)
    published = ArticleManager(public=True)
    drafts = ArticleManager(public=False)

    pub_date = models.DateField(ugettext_lazy(u'Date'), db_index=True)
    pub_time = models.TimeField(ugettext_lazy(u'Time'))
    updated = models.DateTimeField(ugettext_lazy(u'Last change'), blank=True,
                null=True, db_index=True)
    author = models.ForeignKey(User, related_name='article_set',
                               verbose_name=ugettext_lazy(u'Author'))
    subject = models.CharField(ugettext_lazy(u'Headline'), max_length=180)
    category = models.ForeignKey(Category, verbose_name=ugettext_lazy(u'Category'),
                                 on_delete=models.PROTECT)
    icon = models.ForeignKey(StaticFile, blank=True, null=True,
            verbose_name=ugettext_lazy(u'Icon'), on_delete=models.SET_NULL)
    intro = models.TextField(ugettext_lazy(u'Introduction'))
    text = models.TextField(ugettext_lazy(u'Text'))
    public = models.BooleanField(ugettext_lazy(u'Public'))
    slug = models.SlugField(ugettext_lazy(u'Slug'), max_length=100,
            blank=True, db_index=True)
    is_xhtml = models.BooleanField(ugettext_lazy(u'XHTML Markup'),
                default=False)
    comment_count = models.IntegerField(default=0)
    comments_enabled = models.BooleanField(ugettext_lazy(u'Allow comments'),
                        default=True)

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
        return simple

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

    def get_absolute_url(self, action='show', **query):
        if action == 'comments':
            query['_anchor'] = 'comments'
            return href('ikhaya', self.stamp, self.slug, **query)
        if action == 'last_comment':
            query['_anchor'] = 'comment_%d' % self.comment_count
            return href('ikhaya', self.stamp, self.slug, **query)
        if action in ('subscribe', 'unsubscribe'):
            if current_request:
                current = current_request.build_absolute_uri()
                if not self.get_absolute_url() in current:
                    # We may be at the ikhaya index page.
                    if 'next' not in query:
                        query['next'] = current_request.build_absolute_uri()
                    return href('ikhaya', self.stamp, self.slug, action, **query)
            return href('ikhaya', self.stamp, self.slug, action, **query)

        links = {
            'delete':     ('ikhaya', self.stamp, self.slug, 'delete'),
            'edit':       ('ikhaya', self.stamp, self.slug, 'edit'),
            'id':         ('portal', 'ikhaya',  self.id),
            'report_new': ('ikhaya', self.stamp, self.slug, 'new_report'),
            'reports':    ('ikhaya', self.stamp, self.slug, 'reports'),
            'show':       ('ikhaya', self.stamp, self.slug),
        }

        return href(*links[action if action in links.keys() else 'show'], **query)

    def __unicode__(self):
        return self.subject

    def update_search(self):
        """
        This updates the xapian search index.
        """
        IkhayaSearchAdapter.queue(self.id)

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
        self.update_search()

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
        # update search
        self.update_search()

    class Meta:
        verbose_name = ugettext_lazy('Article')
        verbose_name_plural = ugettext_lazy('Articles')
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
    title = models.CharField(ugettext_lazy(u'Title'), max_length=100)
    text = models.TextField(ugettext_lazy(u'Text'))
    intro = models.TextField(ugettext_lazy(u'Introduction'))
    notes = models.TextField(ugettext_lazy(u'Annotations'), blank=True,
                default=u'')
    owner = models.ForeignKey(User, related_name='owned_suggestion_set',
                              null=True, blank=True)

    class Meta:
        verbose_name = ugettext_lazy(u'Article suggestion')
        verbose_name_plural = ugettext_lazy(u'Article suggestions')

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
    location_lat = models.FloatField(ugettext_lazy(u'Degree of latitude'),
                                     blank=True, null=True)
    location_long = models.FloatField(ugettext_lazy(u'Degree of longitude'),
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

    def friendly_title(self, with_html_link=False):
        s_location = '<span class="location">%s</span>' % (
             self.location_town and u' in %s' % self.location_town or '')
        summary = u'<span class="summary">%s</span>' % escape(self.name)
        if with_html_link:
            ret = u'<a href="%s" class="event_link">%s</a>%s' % (
                escape(self.get_absolute_url()),
                summary,
                s_location)
        else:
            ret = summary + s_location
        return u'<span class="vevent">%s</span>' % ret

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


class ArticleSearchAuthDecider(object):
    """Decides whether a user can display a search result or not."""

    def __init__(self, user):
        self.now = datetime.utcnow()
        self.priv = user.can('article_read')

    def __call__(self, auth):
        if not isinstance(auth[1], datetime):
            # this is a workaround for old data in search-index.
            auth = list(auth)
            auth[1] = datetime(auth[1].year, auth[1].month, auth[1].day)
            auth = tuple(auth)
        return self.priv or ((not auth[0]) and auth[1] <= self.now)


class IkhayaSearchAdapter(SearchAdapter):
    type_id = 'i'
    auth_decider = ArticleSearchAuthDecider

    def get_objects(self, docids):
        return Article.objects.select_related(depth=1) \
                      .filter(id__in=docids).all()

    def store_object(self, article, connection=None):
        search.store(connection,
            component='i',
            uid=article.id,
            title=article.subject,
            user=article.author_id,
            date=article.pub_datetime,
            auth=(article.hidden, article.pub_datetime),
            category=article.category.slug,
            text=[article.intro, article.text]
        )

    def extract_data(self, article):
        return {'title': article.subject,
                'user': article.author.username,
                'date': article.pub_datetime,
                'url': url_for(article),
                'component': u'Ikhaya',
                'group': article.category.name,
                'group_url': url_for(article.category),
                'highlight': True,
                'text': u'%s %s' % (article.simplified_intro,
                                    article.simplified_text),
                'hidden': article.hidden,
                'user_url': url_for(article.author)}

    def recv(self, docid):
        article = Article.objects.select_related(depth=1).get(id=docid)
        return self.extract_data(article)

    def recv_multi(self, docids):
        articles = Article.objects.select_related(depth=1).filter(id__in=docids)
        return [self.extract_data(article) for article in articles]

    def get_doc_ids(self):
        ids = Article.objects.values_list('id', flat=True).all()
        for id in ids:
            yield id


#: Register search adapter
search.register(IkhayaSearchAdapter())


#: Register generic model signals
from inyoka.utils import signals
