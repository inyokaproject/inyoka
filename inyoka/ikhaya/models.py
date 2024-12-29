"""
    inyoka.ikhaya.models
    ~~~~~~~~~~~~~~~~~~~~

    Database models for Ikhaya.

    :copyright: (c) 2007-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime
from typing import Optional
from urllib.parse import urlencode

from django.core.cache import cache
from django.db import models
from django.db.models import Q, UniqueConstraint
from django.db.models.functions import Coalesce, TruncDate
from django.utils import timezone as dj_timezone
from django.utils.html import escape
from django.utils.translation import gettext_lazy

from inyoka.portal.models import StaticFile
from inyoka.portal.user import User
from inyoka.utils.database import (
    InyokaMarkupField,
    LockableObject,
    find_next_increment,
)
from inyoka.utils.dates import datetime_to_timezone
from inyoka.utils.decorators import deferred
from inyoka.utils.local import current_request
from inyoka.utils.text import slugify
from inyoka.utils.urls import href


class ArticleManager(models.Manager):

    def __init__(self, public=True, all=False):
        models.Manager.__init__(self)
        self._public = public
        self._all = all

    def get_queryset(self):
        q = super().get_queryset()
        if not self._all:
            q = q.filter(public=self._public)
            if self._public:
                q = q.filter(publication_datetime__lte=dj_timezone.now())
            else:
                q = q.filter(publication_datetime__gte=dj_timezone.now())
        return q

    def get_by_date_and_slug(self, year: int, month: int, day: int, slug: str):
        """Get one article by date and slug
        """
        related = ('author', 'category', 'icon', 'category__icon')
        return Article.objects.select_related(*related).get(slug=slug,
                                                            publication_datetime__year=year,
                                                            publication_datetime__month=month,
                                                            publication_datetime__day=day)

    def get_latest_articles(self, category: Optional[str]=None, count: int=10):
        """Return `count` lastest articles for the category `category` or for
        all categories if None.

        :param category: Takes the slug of the category or None
        :param count: maximum retrieve this many articles. Defaults to 10
        """
        related = ('author', 'category', 'icon', 'category__icon')
        articles = Article.published.select_related(*related).order_by(Coalesce("updated", "publication_datetime").desc())
        if category:
            articles = articles.filter(category__slug=category)

        return articles[:count]


class SuggestionManager(models.Manager):

    def delete(self, ids):
        """
        Deletes a list of suggestions with only one query and refresh the caches.
        """
        Suggestion.objects.filter(id__in=ids).delete()
        cache.delete('ikhaya/suggestion_count')


class CommentManager(models.Manager):

    def get_latest_comments(self, article=None, count=10):
        filter_kwargs = {
            'article__public': True,
            'deleted': False,
        }
        if article:
            filter_kwargs['article'] = article

        comments = Comment.objects.filter(**filter_kwargs).select_related('author', 'article').order_by('-id')
        return comments[:count]


class EventManager(models.Manager):

    def get_upcoming(self, count=10):
        return self.get_queryset().order_by('date').filter(Q(visible=True) & (
            (Q(enddate__gte=dj_timezone.now()) & Q(date__lte=dj_timezone.now())) |
            (Q(date__gte=dj_timezone.now()))))[:count]


class Category(models.Model):
    name = models.CharField(max_length=180)
    slug = models.CharField(gettext_lazy('Slug'), max_length=100,
            blank=True, unique=True, db_index=True)
    icon = models.ForeignKey(StaticFile, blank=True, null=True,
                             verbose_name=gettext_lazy('Icon'), on_delete=models.SET_NULL)

    def __str__(self):
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

        super().save(*args, **kwargs)

        cache.delete('ikhaya/categories')

    class Meta:
        ordering = ('name',)
        verbose_name = gettext_lazy('Category')
        verbose_name_plural = gettext_lazy('Categories')


class Article(models.Model, LockableObject):
    lock_key_base = 'ikhaya/article_lock'

    objects = ArticleManager(all=True)
    published = ArticleManager(public=True)

    publication_datetime = models.DateTimeField(gettext_lazy('Publication time'), default=dj_timezone.now)
    updated = models.DateTimeField(gettext_lazy('Last change'), blank=True,
                null=True, db_index=True,
                help_text=gettext_lazy('If you keep this field empty, the '
                                       'publication date will be used.')
    )
    author = models.ForeignKey(User, related_name='article_set',
                               verbose_name=gettext_lazy('Author'), on_delete=models.CASCADE)
    subject = models.CharField(gettext_lazy('Headline'), max_length=180)
    category = models.ForeignKey(Category, verbose_name=gettext_lazy('Category'),
                                 on_delete=models.PROTECT)
    icon = models.ForeignKey(StaticFile, blank=True, null=True,
            verbose_name=gettext_lazy('Icon'), on_delete=models.SET_NULL)
    intro = InyokaMarkupField(verbose_name=gettext_lazy('Introduction'), application='ikhaya')
    text = InyokaMarkupField(verbose_name=gettext_lazy('Text'), application='ikhaya')
    public = models.BooleanField(gettext_lazy('Public'), default=False)
    slug = models.SlugField(gettext_lazy('Slug'), max_length=100,
            blank=True, db_index=True, help_text=gettext_lazy('Unique URL-part for the article. If not given, the slug will be generated from title.'))
    is_xhtml = models.BooleanField(gettext_lazy('XHTML Markup'),
                default=False)
    comment_count = models.IntegerField(default=0)
    comments_enabled = models.BooleanField(gettext_lazy('Allow comments'),
                        default=True)

    def get_intro(self):
        if self.is_xhtml:
            return self.intro
        return self.intro_rendered

    def get_text(self):
        if self.is_xhtml:
            return self.text
        return self.text_rendered

    @property
    def article_icon(self):
        return self.icon or self.category.icon

    @deferred
    def pub_datetime(self):
        return self.publication_datetime

    @property
    def local_pub_datetime(self):
        return datetime_to_timezone(self.publication_datetime)

    @property
    def local_updated(self):
        return datetime_to_timezone(self.updated)

    @property
    def hidden(self):
        """
        This returns a boolean whether this article is not visible for normal
        users.
        Article that are not published or whose publication date is in the future
        aren't shown for a normal user.
        """
        return not self.public or self.publication_datetime > dj_timezone.now()

    @property
    def is_updated(self) -> bool:
        """
        Returns whether this article has an update (f.e. a addition was made or a big mistake fixed)
        """
        if not self.updated:
            return False

        return self.updated > self.publication_datetime

    @property
    def comments(self):
        """This returns all the comments for this article"""
        return Comment.objects.filter(article=self)

    @property
    def stamp(self):
        """Return the year/month/day part of an article url"""
        return self.publication_datetime.strftime('%Y/%m/%d')

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
                if self.get_absolute_url() not in current:
                    # We may be at the ikhaya index page.
                    if 'next' not in query:
                        query['next'] = current_request.build_absolute_uri()
                    return href('ikhaya', self.stamp, self.slug, action, **query)
            return href('ikhaya', self.stamp, self.slug, action, **query)

        links = {
            'delete': ('ikhaya', self.stamp, self.slug, 'delete'),
            'edit': ('ikhaya', self.stamp, self.slug, 'edit'),
            'id': ('portal', 'ikhaya', self.id),
            'report_new': ('ikhaya', self.stamp, self.slug, 'new_report'),
            'reports': ('ikhaya', self.stamp, self.slug, 'reports'),
            'show': ('ikhaya', self.stamp, self.slug),
        }

        return href(*links[action if action in list(links.keys()) else 'show'], **query)

    def __str__(self):
        return self.subject

    def save(self, *args, **kwargs):
        if self.text is None or self.intro is None:
            # might happen, because cached objects are setting text and
            # intro to None to save some space
            raise ValueError('text and intro must not be null')

        if not self.slug:
            self.slug = find_next_increment(Article, 'slug',
                                            slugify(self.subject),
                                            publication_datetime__date=self.publication_datetime,
                                            )
        else:
            self.slug = slugify(self.slug)

        super().save(*args, **kwargs)

        cache.delete('ikhaya/archive')

    def delete(self):
        """
        Subscriptions are removed by a Django signal `pre_delete`
        """
        id = self.id
        super().delete()
        self.id = id

    class Meta:
        verbose_name = gettext_lazy('Article')
        verbose_name_plural = gettext_lazy('Articles')
        ordering = ['-publication_datetime', 'author']
        constraints = [
            UniqueConstraint(TruncDate('publication_datetime'), 'slug', name='unique_pub_date_slug'),
        ]
        permissions = (
            ('view_unpublished_article', 'Can view unpublished articles'),
            ('suggest_article', 'Can suggest articles'),
        )


class Report(models.Model):
    article = models.ForeignKey(Article, null=True, on_delete=models.CASCADE)
    text = InyokaMarkupField(application='ikhaya')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    pub_date = models.DateTimeField()
    deleted = models.BooleanField(null=False, default=False)
    solved = models.BooleanField(null=False, default=False)

    def __repr__(self):
        subject = self.article.subject if self.article else '?'
        if self.pk is None:
            return '<Report on %r>' % subject
        return '<Report #%d on %r>' % (self.pk, subject)

    def get_absolute_url(self, action='show'):
        if action == 'show':
            return href('ikhaya', self.article.stamp, self.article.slug, 'reports')
        return href('ikhaya', 'report', self.id, action)


class Suggestion(models.Model):

    objects = SuggestionManager()

    author = models.ForeignKey(User, related_name='suggestion_set', on_delete=models.CASCADE)
    pub_date = models.DateTimeField('Datum', default=dj_timezone.now)
    title = models.CharField(gettext_lazy('Title'), max_length=100)
    text = InyokaMarkupField(verbose_name=gettext_lazy('Text'), application='ikhaya')
    intro = InyokaMarkupField(verbose_name=gettext_lazy('Introduction'), application='ikhaya')
    notes = InyokaMarkupField(
        verbose_name=gettext_lazy('Annotations to the team'),
        blank=True,
        default='',
        application='ikhaya')
    owner = models.ForeignKey(User, related_name='owned_suggestion_set',
                              null=True, blank=True, on_delete=models.CASCADE)

    class Meta:
        verbose_name = gettext_lazy('Article suggestion')
        verbose_name_plural = gettext_lazy('Article suggestions')

    def get_absolute_url(self):
        return href('ikhaya', 'suggestions', _anchor=self.id)


class Comment(models.Model):

    objects = CommentManager()

    article = models.ForeignKey(Article, null=True, on_delete=models.CASCADE)
    text = InyokaMarkupField(application='ikhaya')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    pub_date = models.DateTimeField()
    deleted = models.BooleanField(null=False, default=False)

    class Meta:
        ordering = ['id']

    def get_absolute_url(self, action='show'):
        if action in ['hide', 'restore', 'edit']:
            return href('ikhaya', 'comment', self.id, action)
        return href('ikhaya', self.article.stamp, self.article.slug,
                    _anchor=f'comment_{ self.position }')

    @property
    def position(self):
        """Returns the position/index of this comment below an article"""
        position = self.article.comment_set.filter(id__lt=self.id).count()
        return position + 1

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.article = Article.objects.get(id=self.article.id)
            self.article.comment_count = self.article.comment_count + 1
            self.article.save()

        super().save(*args, **kwargs)

        if self.id:
            cache.delete(f'ikhaya/comment/{self.id}')


class Event(models.Model):
    objects = EventManager()

    name = models.CharField(gettext_lazy('Name'), max_length=50)
    slug = models.SlugField(unique=True, max_length=100, db_index=True)
    changed = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    date = models.DateField(gettext_lazy('Date (from)'), db_index=True)
    time = models.TimeField(gettext_lazy('Time (from)'), blank=True, null=True)  # None -> whole day
    enddate = models.DateField(gettext_lazy('Date (to)'), blank=True, null=True)  # None
    endtime = models.TimeField(gettext_lazy('Time (to)'), blank=True, null=True)  # None -> whole day
    description = InyokaMarkupField(verbose_name=gettext_lazy('Description'), blank=True, application='ikhaya')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    location = models.CharField(gettext_lazy('Venue'), max_length=128, blank=True)
    location_town = models.CharField(gettext_lazy('Town'), max_length=56, blank=True)
    location_lat = models.FloatField(gettext_lazy('Degree of latitude'),
                                     blank=True, null=True)
    location_long = models.FloatField(gettext_lazy('Degree of longitude'),
                                      blank=True, null=True)
    visible = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def get_absolute_url(self, action='show'):
        if action == 'copy':
            return href('ikhaya', 'event', 'new', copy_from=self.id)
        return href(*{
            'show': ('portal', 'calendar', self.slug),
            'delete': ('ikhaya', 'event', self.id, 'delete'),
            'edit': ('ikhaya', 'event', self.id, 'edit'),
            'new': ('ikhaya', 'event', 'new'),
        }[action])

    def save(self, *args, **kwargs):
        if not self.slug:
            name = self.date.strftime('%Y/%m/%d/') + slugify(self.name)
            self.slug = find_next_increment(Event, 'slug', name)

        super().save(*args, **kwargs)

        cache.delete(f'ikhaya/event/{self.id}')
        cache.delete('ikhaya/event_count')

    def friendly_title(self, with_html_link=False):
        s_location = '<span class="location">%s</span>' % (
            self.location_town and ' in %s' % self.location_town or '')
        summary = '<span class="summary">%s</span>' % escape(self.name)
        if with_html_link:
            ret = '<a href="%s" class="event_link">%s</a>%s' % (
                escape(self.get_absolute_url()),
                summary,
                s_location)
        else:
            ret = summary + s_location
        return '<span class="vevent">%s</span>' % ret

    @property
    def natural_coordinates(self):
        if self.location_lat and self.location_long:
            latitude = (self.location_lat > 0 and
                   '%g° N' % self.location_lat or
                   '%g° S' % -self.location_lat)
            longitude = (self.location_long > 0 and
                    '%g° O' % self.location_long or
                    '%g° W' % -self.location_long)
            return '%s, %s' % (latitude, longitude)
        else:
            return ''

    @property
    def simple_coordinates(self):
        return '%s;%s' % (self.location_lat, self.location_long)

    @property
    def coordinates_url(self) -> Optional[str]:
        """Create a link to openstreetmap that shows details to a provided location"""
        if not self.location_long or not self.location_lat:
            return None

        query_parameter = {
            'mlat': self.location_lat,
            'mlon': self.location_long,
        }
        query_parameter = urlencode(query_parameter)

        return f'https://www.openstreetmap.org/?{query_parameter}'

    def _construct_datetimes(self, day, time):
        if not day:
            day = dj_timezone.localdate() ## TODO check
        return datetime_to_timezone(datetime.combine(day, time))

    @property
    def startdatetime(self):
        return self._construct_datetimes(self.date, self.time)

    @property
    def enddatetime(self):
        return self._construct_datetimes(self.enddate or self.date, self.endtime)

    class Meta:
        db_table = 'portal_event'
        app_label = 'portal'
        permissions = (
            ('suggest_event', 'Can suggest events'),
        )
