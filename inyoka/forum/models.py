# -*- coding: utf-8 -*-
"""
    inyoka.forum.models
    ~~~~~~~~~~~~~~~~~~~

    Database models for the forum.

    :copyright: (c) 2007-2014 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import division

import re
import cPickle
import operator
from os import path
from time import time
from hashlib import md5
from datetime import datetime
from operator import attrgetter, itemgetter
from functools import reduce
from itertools import groupby

from django.db import models, transaction
from django.conf import settings
from django.db.models import F, Max, Count
from django.utils.html import escape
from django.core.cache import cache
from django.utils.encoding import force_unicode, DjangoUnicodeDecodeError
from django.utils.html import escape, format_html
from django.utils.translation import pgettext, ugettext as _, ugettext_lazy
from django.contrib.contenttypes.models import ContentType

from inyoka.forum.acl import (CAN_READ, get_privileges, filter_visible,
    check_privilege, filter_invisible)
from inyoka.forum.constants import (CACHE_PAGES_COUNT, POSTS_PER_PAGE,
    SUPPORTED_IMAGE_TYPES, UBUNTU_DISTROS_LEGACY)
from inyoka.markup import parse, RenderContext
from inyoka.portal.models import SearchQueue, Subscription
from inyoka.portal.user import User, Group
from inyoka.portal.utils import get_ubuntu_versions
from inyoka.utils.cache import request_cache
from inyoka.utils.database import update_model, model_or_none, LockableObject
from inyoka.utils.dates import timedelta_to_seconds
from inyoka.utils.decorators import deferred
from inyoka.utils.files import get_filename
from inyoka.utils.highlight import highlight_code
from inyoka.utils.imaging import get_thumbnail
from inyoka.utils.local import current_request
from inyoka.utils.pagination import Pagination
from inyoka.utils.search import search
from inyoka.utils.urls import href
from inyoka.wiki.models import Page as WikiPage

_newline_re = re.compile(r'\r?\n')


def fix_plaintext(text):
    text = escape(text)
    text = _newline_re.sub('<br />', text)
    return text


class ForumManager(models.Manager):

    def get_slugs(self):
        """Return a slug map.

        The slug map is a dictionary of {Forum.id: Forum.slug} and is retrieved
        from cache.
        """
        slug_map = request_cache.get('forum/slugs')
        if slug_map is None:
            slug_map = dict(Forum.objects.values_list('id', 'slug'))
            request_cache.set('forum/slugs', slug_map, 86400)
        return slug_map

    def get_ids(self):
        """Return all forum ids from cache."""
        return self.get_slugs().keys()

    def get(self, ident=None, slug=None, id=None):
        """Unified .get method that accepts either a id or a slug.

        The forum object is retrieved from cache whenever possible.
        """
        ident = ident or slug or id

        # We unify the usage internally to query the id but accept an slug too.
        # To cache the result we use the slug as it's used in the forum view too
        slugs = self.get_slugs()

        if isinstance(ident, (int, float, long)):
            ident = slugs.get(ident)

        if ident is None:
            return None

        forum = self.get_cached(ident)
        return forum

    def get_all_forums_cached(self):
        """Return all forum objects from cache.

        Every forum is retrieved from cache, if it's not yet cached
        it is stored in the cache afterwards.
        """
        slugs = self.get_slugs()
        reverted = {str(y): x for x, y in slugs.iteritems()}
        cache_keys = ['forum/forums/%s' % s for s in reverted]
        forums = cache.get_many(cache_keys)

        # fill forum cache
        missing = [reverted[key.split('/')[-1]] for key in cache_keys
                   if key not in forums]
        if missing:
            query = self.get_query_set()
            # If we query all forums, and all forums are missing we don't
            # need to use an IN (...) expression, allows us to use indexed scans.
            if not len(missing) == len(slugs):
                query = query.filter(id__in=missing)
            for forum in query:
                forums['forum/forums/%s' % forum.slug] = forum
            cache.set_many(forums, 300)

        return forums

    def get_cached(self, slug=None):
        """Return either all or one forum from cache.

        :param slug: If slug is given only one forum is returned.
                     If slug is `None` (default) all forums get returned.
        """
        if slug:
            # we only select one forum and query only one if it's
            # not cached yet.
            forum = cache.get('forum/forums/%s' % slug)
            if forum is None:
                forum = super(ForumManager, self).get(slug=slug)
                if forum:
                    forum.__dict__.pop('last_post', None)
                    cache.set('forum/forums/%s' % slug, forum, 300)
            return forum
        # return all forums instead
        return self.get_all_forums_cached().values()

    def get_forums_filtered(self, user, priv=CAN_READ, reverse=False, sort=False):
        """Return all forums the `user` has proper privileges for.

        :param user: :class:`User` instance.
        :param priv: A bit reresenting a privilege, see :mod:`inyoka.forum.acl`
        :param reverse: Reverse the filtering (visible/unvisible), default is
                        that only visible forums are returned.
        :param sort: Sort the output by position.
        """
        if sort:
            forums = self.get_sorted()
        else:
            forums = self.get_cached()

        privileges = get_privileges(user, forums)
        if reverse:
            forums = filter_visible(user, forums, priv, privileges)
        else:
            forums = filter_invisible(user, forums, priv, privileges)
        return forums

    def get_categories(self):
        return self.get_query_set().filter(parent=None)

    def get_sorted(self, reverse=False, attr='position'):
        forums = self.get_cached()
        forums = sorted(forums, key=attrgetter(attr))
        return forums


class TopicManager(models.Manager):

    def prepare_for_overview(self, topic_ids):
        related = ('author', 'last_post', 'last_post__author', 'first_post',
                   'first_post__author')
        order = ('-sticky', '-last_post__id')
        return self.get_query_set().filter(pk__in=topic_ids) \
                   .select_related(*related).order_by(*order)

    def get_latest(self, forum_slug=None, allowed_forums=None, count=10):
        """
        Return a list of the latest topics in this forum. If no count is
        given the default value from the settings will be used and the whole
        output will be partly cached (highly recommended!).

        The returned objects do not include hidden objects and sticky objects
        aren't at the top!
        """
        key = 'forum/latest_topics'
        forum = None
        if forum_slug is not None:
            key = 'forum/latest_topics/%s' % forum_slug
            forum = Forum.objects.get_cached(forum_slug)

        topic_ids = cache.get(key)
        if topic_ids is None:
            query = Topic.objects.filter(hidden=False)
            if forum_slug:
                query = query.filter(forum__id=forum.id)
            if allowed_forums:
                query = query.filter(forum__id__in=(allowed_forums))

            maxcount = max(settings.AVAILABLE_FEED_COUNTS['forum_forum_feed'])
            topic_ids = list(query.order_by('-id').values_list('id', flat=True)[:maxcount])
            cache.set(key, topic_ids, 300)

        related = ('author', 'last_post', 'last_post__author', 'first_post')
        topics = Topic.objects.filter(id__in=topic_ids) \
                              .order_by('-last_post__id') \
                              .select_related(*related).all()
        return topics[:count]


class Forum(models.Model):
    """This is a forum that may contain subforums or topics.

    If parent is `None` this forum is a category, else it's a common forum
    that can contain topics.  Position is an integer that's used to sort
    the forums.  The lower position is, the higher the forum is displayed.
    """
    objects = ForumManager()

    name = models.CharField(max_length=100)
    slug = models.CharField(max_length=100, unique=True, db_index=True)
    description = models.CharField(max_length=500, blank=True)
    position = models.IntegerField(default=0, db_index=True)
    post_count = models.IntegerField(default=0)
    topic_count = models.IntegerField(default=0)
    newtopic_default_text = models.TextField(null=True, blank=True)
    user_count_posts = models.BooleanField(default=True)
    force_version = models.BooleanField(default=False)

    parent = models.ForeignKey('self', null=True, related_name='_children',
        on_delete=models.PROTECT)
    last_post = models.ForeignKey('forum.Post', null=True, blank=True,
        on_delete=models.PROTECT)
    welcome_message = models.ForeignKey('forum.WelcomeMessage', null=True,
        blank=True, on_delete=models.SET_NULL)

    class Meta:
        verbose_name = ugettext_lazy(u'Forum')
        verbose_name_plural = ugettext_lazy(u'Forums')

    def get_absolute_url(self, action='show', **query):
        if action == 'show':
            return href('forum', self.parent_id and 'forum' or 'category',
                        self.slug, **query)
        if action in ('newtopic', 'welcome', 'subscribe', 'unsubscribe',
                      'markread'):
            return href('forum', 'forum', self.slug, action, **query)
        if action == 'edit':
            return href('forum', 'forum', self.slug, 'edit', **query)

    def get_parents(self, cached=True):
        """Return a list of all parent forums up to the root level."""
        parents = []
        forums = Forum.objects.get_cached() if cached else \
                 Forum.objects.all()
        qdct = {forum.id: forum for forum in forums}

        forum = qdct[self.id]
        while forum.parent_id is not None:
            forum = qdct[forum.parent_id]
            parents.append(forum)
        return parents

    @property
    def parents(self):
        return self.get_parents(True)

    @property
    def children(self):
        forums = Forum.objects.get_cached()
        children = [forum for forum in forums if forum.parent_id == self.id]
        return children

    def filter_children(self, forums):
        return [forum for forum in forums if forum.parent_id == self.id]

    def get_read_status(self, user):
        """
        Determine the read status of the whole forum for a specific
        user.
        """
        if user.is_anonymous:
            return True
        return user._readstatus(self)

    def mark_read(self, user):
        """
        Mark all topics in this forum and all related subforums as
        read for the specificed user.
        """
        if user.is_anonymous:
            return
        if user._readstatus.mark(self):
            user.forum_read_status = user._readstatus.serialize()
            user.save(update_fields=('forum_read_status',))

    def find_welcome(self, user):
        """
        Return a forum with an unread welcome message if exits.
        The message itself, can be retrieved late, by reading the
        welcome_message attribute.
        """
        forums = self.parents
        forums.append(self)
        read = set()
        if user.is_authenticated() and user.forum_welcome:
            read = set(int(i) for i in user.forum_welcome.split(','))
        for forum in forums:
            if forum.welcome_message is not None and forum.id not in read:
                return forum
        return None

    def read_welcome(self, user, read=True):
        if user.is_anonymous:
            return
        status = set()
        if user.forum_welcome:
            status = set(int(i) for i in user.forum_welcome.split(','))
        if read:
            status.add(self.id)
        else:
            status.discard(self.id)
        user.forum_welcome = ','.join(str(id) for id in status)
        user.save(update_fields=('forum_welcome',))

    def invalidate_topic_cache(self):
        cache.delete_many('forum/topics/%d/%d' % (self.id, page + 1) for page in
            range(CACHE_PAGES_COUNT))

    @staticmethod
    def get_children_recursive(forums, parent=None, offset=0):
        """
        Yield all forums sorted as in the index page, with indentation.
        `forums` must be sorted by position.
        Every entry is a tuple (offset, forum). Example usage::

            forums = Forum.objects.order_by('-position').all()
            for offset, f in Forum.get_children_recursive(forums):
                choices.append((f.id, u'  ' * offset + f.name))
        """
        if isinstance(parent, Forum):
            parent = parent.id
        matched_forums = filter(lambda f: f.parent_id == parent, forums)
        for f in matched_forums:
            yield offset, f
            for l in Forum.get_children_recursive(forums, f, offset + 1):
                yield l

    def get_supporters(self):
        supporters = cache.get('forum/forum/supporters-%s' % self.id)
        if supporters is None:
            supporters = []
            query = Privilege.objects \
                             .filter(forum__id=self.id, user__id__isnull=False) \
                             .values_list('user__id', 'positive')
            subset = [priv[0] for priv in query if check_privilege(priv[1], 'moderate')]
            if subset:
                supporters = list(User.objects.defer('settings', 'forum_read_status') \
                    .filter(id__in=subset).order_by('username').all())
            cache.set('forum/forum/supporters-%s' % self.id, supporters, 86400)
        return supporters

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return '<%s #%s pos=%d>' % (
            self.__class__.__name__,
            self.id,
            self.position,
        )


class Topic(models.Model):
    """A topic symbolizes a bunch of posts (at least one) that is located
    insside a forum.  Wen creating a new topic, a new post is added to it
    automatically.
    """
    objects = TopicManager()

    title = models.CharField(max_length=100, blank=True)
    slug = models.CharField(max_length=50, blank=True)
    view_count = models.IntegerField(default=0)
    post_count = models.IntegerField(default=0)
    sticky = models.BooleanField(default=False, db_index=True)
    solved = models.BooleanField(default=False)
    locked = models.BooleanField(default=False)
    reported = models.TextField(blank=True, null=True)
    hidden = models.BooleanField(default=False)
    ubuntu_version = models.CharField(max_length=5, null=True, blank=True)
    ubuntu_distro = models.CharField(max_length=40, null=True, blank=True)
    has_poll = models.BooleanField(default=False)

    forum = models.ForeignKey(Forum, related_name='topics',
        on_delete=models.PROTECT)
    reporter = models.ForeignKey(User, null=True, related_name='+',
        on_delete=models.PROTECT)
    report_claimed_by = models.ForeignKey(User, null=True, related_name='+',
        on_delete=models.PROTECT)
    author = models.ForeignKey(User, related_name='topics',
        on_delete=models.PROTECT)
    first_post = models.ForeignKey('forum.Post', null=True, related_name='+',
        on_delete=models.PROTECT)
    last_post = models.ForeignKey('forum.Post', null=True, related_name='+',
        on_delete=models.PROTECT)

    class Meta:
        verbose_name = ugettext_lazy(u'Topic')
        verbose_name_plural = ugettext_lazy(u'Topics')

    @property
    def rendered_report_text(self):
        return parse(self.reported).render(None, 'html')

    def cached_forum(self):
        return Forum.objects.get(self.forum_id)

    def touch(self):
        """Increment the view count in a safe way."""
        Topic.objects.filter(id=self.id).update(view_count=F('view_count') + 1)

    def move(self, new_forum):
        """Move the topic to an other forum."""
        old_forums = [parent for parent in self.forum.parents]
        old_forums.append(self.forum)
        new_forums = [parent for parent in new_forum.parents]
        new_forums.append(new_forum)

        old_forum = self.forum

        with transaction.commit_on_success():

            # move the topic
            self.forum = new_forum

            # recalculate post counters
            new_forum.topic_count += 1
            old_forum.topic_count -= 1

            for forum in new_forums:
                forum.post_count += 1

            for forum in old_forums:
                forum.post_count -= 1

            # Decrement or increment the user post count regarding
            # posts are counted in the new forum or not.
            if old_forum.user_count_posts != new_forum.user_count_posts:
                if new_forum.user_count_posts and not old_forum.user_count_posts:
                    op = operator.add
                elif not new_forum.user_count_posts and old_forum.user_count_posts:
                    op = operator.sub

                post_counts = User.objects.filter(post__topic__id=self.id).distinct() \
                                          .annotate(pcount=Count('post__id'))

                for user in post_counts:
                    user.post_count = op(user.post_count, user.pcount)
                    user.save(update_fields=('post_count',))

            self.save()

            # and find a new last post id for the new forum
            new_ids = [p.id for p in new_forums]
            old_ids = [p.id for p in old_forums]

            # search for a new last post in the old and the new forum
            new_post_query = Post.objects.filter(
                topic__id=F('topic__id'),
                topic__forum__id=F('topic__forum__id'))

            Forum.objects.filter(id__in=new_ids).update(
                last_post=new_post_query._clone().filter(forum__id__in=new_ids) \
                                                 .aggregate(count=Max('id'))['count'])

            Forum.objects.filter(id__in=old_ids).update(
                last_post=new_post_query._clone().filter(forum__id__in=old_ids) \
                                                 .aggregate(count=Max('id'))['count'])

        old_forum.invalidate_topic_cache()
        new_forum.invalidate_topic_cache()
        self.reindex()

    def delete(self, *args, **kwargs):
        if not self.forum:
            return super(Topic, self).delete()

        forums = self.forum.parents + [self]
        pks = [f.pk for f in forums]

        last_post = Post.objects.filter(topic__id=F('topic__id'),
                                        topic__forum__pk__in=pks) \
                                .aggregate(count=Max('id'))['count']

        update_model(forums, last_post=model_or_none(last_post, self.last_post))
        update_model(self, last_post=None, first_post=None)
        update_model(self.forum, topic_count=F('topic_count') - 1)

        for post in self.posts.all():
            post.delete()

        # Delete subscriptions and remove wiki page discussions
        ctype = ContentType.objects.get_for_model(Topic)
        Subscription.objects.filter(content_type=ctype, object_id=self.id).delete()
        WikiPage.objects.filter(topic=self).update(topic=None)
        return super(Topic, self).delete()

    def get_absolute_url(self, action='show', **query):
        if action in ('show',):
            return href('forum', 'topic', self.slug, **query)
        if action in ('reply', 'delete', 'hide', 'restore', 'split', 'move',
                      'solve', 'unsolve', 'lock', 'unlock', 'report',
                      'report_done', 'subscribe', 'unsubscribe',
                      'first_unread', 'last_post'):
            return href('forum', 'topic', self.slug, action, **query)

    def get_pagination(self):
        request = current_request._get_current_object()
        pagination = Pagination(request=request, query=[], page=1, total=self.post_count,
                                per_page=POSTS_PER_PAGE, link=self.get_absolute_url())
        return pagination

    @property
    def paginated(self):
        return bool((self.post_count - 1) // POSTS_PER_PAGE)

    def get_ubuntu_version(self):
        if self.ubuntu_version:
            version = filter(lambda v: v.number == self.ubuntu_version, get_ubuntu_versions())
            if len(version) > 0:
                return version[0]
            return ''

    def get_version_info(self, default=None):
        if default is None:
            default = _(u'Not specified')
        if not (self.ubuntu_version or self.ubuntu_distro):
            return default
        if self.ubuntu_distro == u'none':
            return _(u'No Ubuntu')
        out = []
        if self.ubuntu_distro:
            out.append(UBUNTU_DISTROS_LEGACY[self.ubuntu_distro])
        if self.ubuntu_version and self.ubuntu_version != u'none':
            out.append(force_unicode(self.get_ubuntu_version()))
        return u' '.join(force_unicode(x) for x in out)

    def get_read_status(self, user):
        if user.is_anonymous:
            return True
        if not hasattr(user, '_readstatus'):
            user._readstatus = ReadStatus(user.forum_read_status)
        return user._readstatus(self)

    def mark_read(self, user):
        """
        Mark the current topic as read for a given user.
        """
        if user.is_anonymous:
            return
        if not hasattr(user, '_readstatus'):
            user._readstatus = ReadStatus(user.forum_read_status)
        if user._readstatus.mark(self):
            user.forum_read_status = user._readstatus.serialize()
            user.save(update_fields=('forum_read_status',))

    def reindex(self):
        """Mark the whole topic for reindexing."""
        posts = Post.objects.filter(topic__id=self.id).values_list('id', flat=True)
        for post in posts:
            search.queue('f', post)

    def __unicode__(self):
        return self.title

    def __repr__(self):
        return '<%s id=%s>' % (
            self.__class__.__name__,
            self.id
        )


class PostRevision(models.Model):
    """This saves old and current revisions of posts.

    It can be used to restore posts if something odd was done
    or to view changes.
    """

    text = models.TextField()
    store_date = models.DateTimeField(default=datetime.utcnow)
    post = models.ForeignKey('forum.Post', related_name='revisions')

    def get_absolute_url(self, action='restore'):
        return href('forum', 'revision', self.id, 'restore')

    @property
    def rendered_text(self):
        if self.post.is_plaintext:
            return fix_plaintext(self.text)
        request = current_request._get_current_object()
        context = RenderContext(request, simplified=False, forum_post=self.post,
                                application='forum')
        return parse(self.text).render(context, 'html')

    def restore(self, request):
        """
        Edits the text of the post the revision belongs to and deletes the
        revision.
        """
        self.post.edit(request, self.text)


class PostManager(models.Manager):
    def last_post_map(self, ids):
        """Return a mapping from post id to `Post` instances.

        This method defers heavy fields.
        """
        last_post_map = {}
        if ids:
            query = self.get_query_set()
            last_posts = query.filter(id__in=ids) \
                .select_related('author') \
                .only('id', 'pub_date', 'author__username').all()
            last_post_map = dict(map(lambda post: (post.id, post), last_posts))
        return last_post_map


class Post(models.Model, LockableObject):
    """Represents a post in a topic."""
    objects = PostManager()
    lock_key_base = 'forum/post_lock'

    position = models.IntegerField(default=None, db_index=True)
    pub_date = models.DateTimeField(default=datetime.utcnow, db_index=True)
    hidden = models.BooleanField(default=False)
    text = models.TextField()
    rendered_text = models.TextField(null=True, blank=True)
    has_revision = models.BooleanField(default=False)
    has_attachments = models.BooleanField(default=False)
    is_plaintext = models.BooleanField(default=False)

    author = models.ForeignKey(User, on_delete=models.PROTECT)
    topic = models.ForeignKey(Topic, related_name='posts',
        on_delete=models.PROTECT)

    class Meta:
        verbose_name = ugettext_lazy(u'Post')
        verbose_name_plural = ugettext_lazy(u'Posts')

    def render_text(self, request=None, format='html', force_existing=False):
        context = RenderContext(request, forum_post=self, application='forum')
        node = parse(self.text, wiki_force_existing=force_existing)
        return node.render(context, format)

    def get_text(self):
        if self.is_plaintext:
            return fix_plaintext(self.text)
        return self.rendered_text

    def update_search(self):
        """
        This updates the xapian search index.
        """
        search.queue('f', self.id)

    def get_absolute_url(self, action='show'):
        if action == 'show':
            return href('forum', 'post', self.id)
        if action == 'fullurl':
            return Post.url_for_post(self.id)
        return href('forum', 'post', self.id, action)

    @staticmethod
    def url_for_post(id, paramstr=None):
        post = Post.objects.get(id=id)
        position, slug = post.position, post.topic.slug
        page = max(0, position) // POSTS_PER_PAGE + 1
        url = href('forum', 'topic', slug, *(page != 1 and (page,) or ()))
        return u''.join((url, paramstr and '?%s' % paramstr or '', '#post-%d' % id))

    @staticmethod
    def multi_update_search(ids):
        """
        Updates the search index for quite a lot of posts with a single query.
        """
        SearchQueue.objects.multi_insert('f', ids)

    def edit(self, request, text, is_plaintext=False):
        """
        Change the text of the post. If the post is already stored in the
        database, create a post revision containing the new text.
        If the text has not changed, return.

        .. note::

            This method saves the current state of the post and it's
            revisions. You do not have to do that yourself.
        """
        if self.text == text and self.is_plaintext == is_plaintext:
            return

        # We need to check for the empty text to prevent a initial empty
        # revision
        if self.pk and self.text.strip():
            # Create a first revision for the initial post
            if not self.has_revision:
                PostRevision(post=self, store_date=self.pub_date,
                             text=self.text).save()
                self.has_revision = True

            PostRevision(post=self, text=text).save()

        self.text = text
        if not is_plaintext:
            self.rendered_text = self.render_text(request)
        else:
            # cleanup that column so that we save some bytes in the database
            self.rendered_text = None
        self.is_plaintext = is_plaintext
        self.save()

    def delete(self, *args, **kwargs):
        """Delete the post and apply environmental changes.

        This method recalculates the post_count, updates the
        last and first posts of all parent forums.

        Note: The cache for all parent forums is explicitely deleted
              to update last/first post properly.
        """
        if not self.topic:
            return super(Post, self).delete()

        # degrade user post count
        if self.topic.forum.user_count_posts:
            update_model(self.author, post_count=F('post_count') - 1)
            cache.delete('portal/user/%d' % self.author.id)

        # update topic.last_post_id
        if self.pk == self.topic.last_post_id:
            new_lp_ids = Post.objects.filter(topic=self.topic)\
                .exclude(pk=self.pk).order_by('-position')\
                .values_list('id', flat=True)
            new_lp_id = new_lp_ids[0] if new_lp_ids else None
            update_model(self.topic, last_post=model_or_none(new_lp_id, self))

        # decrement post_counts
        forums = self.topic.forum.parents + [self.topic.forum]
        update_model(self.topic, post_count=F('post_count') - 1)
        update_model(forums, post_count=F('post_count') - 1)

        # decrement position
        Post.objects.filter(position__gt=self.position, topic=self.topic) \
                    .update(position=F('position') - 1)

        forums = list(Forum.objects.filter(last_post=self).all())

        # search for a new last post for al forums in the chain up.
        # We actually cheat here and set the newest post from the current
        # forum for all forums.
        if self.pk == self.topic.forum.last_post_id:
            new_lp_ids = Topic.objects.filter(forum=self.topic.forum)\
                .exclude(last_post=self).order_by('-last_post')\
                .values_list('last_post', flat=True)
            new_lp_id = new_lp_ids[0] if new_lp_ids else None
            update_model(forums, last_post=model_or_none(new_lp_id, self))
            self.topic.forum.last_post_id = new_lp_id

        cache.delete_many('forum/forums/%s' % f.slug for f in forums)

        return super(Post, self).delete()

    @property
    def page(self):
        """
        this returns None if page is 1, use post.page or 1 if you need number
        """
        page = self.position // POSTS_PER_PAGE + 1
        if page == 1:
            return None
        return page

    @staticmethod
    def split(posts, old_topic, new_topic):
        """
        This function splits `posts` out of `old_topic` and moves them into
        `new_topic`.
        It is important that `posts` is a list of posts ordered by id
        ascending.
        """
        remove_topic = False
        posts = sorted(list(posts), key=attrgetter('position'))

        old_forums = [parent for parent in old_topic.forum.parents]
        old_forums.append(old_topic.forum)
        new_forums = [parent for parent in new_topic.forum.parents]
        new_forums.append(new_topic.forum)

        if len(posts) == old_topic.posts.count():
            # The user selected to split all posts out of the topic -->
            # delete the topic.
            remove_topic = True

        with transaction.commit_on_success():
            maxpos = new_topic.posts.all()._clone() \
                              .aggregate(count=Max('position'))['count']
            if maxpos is None:
                # New topic. First post must get the position 0
                maxpos = -1

            post_ids = map(lambda p: p.id, posts)
            Post.objects.filter(pk__in=post_ids).update(topic=new_topic)
            for post in posts:
                maxpos += 1
                Post.objects.filter(pk=post.pk).update(position=maxpos)

            # adjust positions of the old topic.
            # split the posts into continous groups
            post_groups = [(v.position - k, v) for k, v in enumerate(posts)]
            post_groups = groupby(post_groups, itemgetter(0))

            adjust_start = 0
            # decrement the old positions
            for x, g in post_groups:
                g = list(g)
                dec = len(g)
                # and don't forget that previous decrements already decremented our position
                start = g[-1][1].position - adjust_start
                Post.objects.filter(topic=old_topic, position__gt=start)\
                    .update(position=F('position') - dec)
                adjust_start += dec

            if old_topic.forum.id != new_topic.forum.id:
                # Decrease the post counts in the old forum (counter in the new
                # one are handled by signals)
                old_topic.forum.post_count -= len(posts)

                # the new forum or not.
                new_forum, old_forum = new_topic.forum, old_topic.forum
                if old_forum.user_count_posts != new_forum.user_count_posts:
                    if new_forum.user_count_posts and not old_forum.user_count_posts:
                        op = operator.add
                    elif not new_forum.user_count_posts and old_forum.user_count_posts:
                        op = operator.sub

                    post_counts = User.objects.filter(post__in=posts).values('id') \
                                              .annotate(pcount=Count('post__id'))
                    for user in post_counts:
                        User.objects.filter(pk=user['id']) \
                                .update(post_count=op(F('post_count'), user['pcount']))
                    cache.delete_many('portal/user/%d' % user['id'] for user in post_counts)

            if not remove_topic:
                Topic.objects.filter(pk=old_topic.pk) \
                             .update(post_count=F('post_count') - len(posts),
                                     last_post=old_topic.posts.order_by('-position')[0])
            else:
                if old_topic.has_poll:
                    new_topic.has_poll = True
                    Poll.objects.filter(topic=old_topic).update(topic=new_topic)
                new_topic.last_post = new_topic.posts.order_by('-position')[0]
                old_topic.delete()

            values = {'last_post': sorted(posts, key=lambda o: o.position)[-1],
                      'post_count': new_topic.posts.count(),
                      'first_post': new_topic.first_post}
            if new_topic.first_post is None:
                values['first_post'] = sorted(posts, key=lambda o: o.position)[0]
            Topic.objects.filter(pk=new_topic.pk).update(**values)
            Post.objects.filter(pk=values['first_post'].pk).update(position=0)

            # and find a new last post id for the new forum
            new_ids = [p.id for p in new_forums]
            old_ids = [p.id for p in old_forums]

            # Update last_post of the forums
            # NOTE: last_post of a forum is expected to be the most recent post,
            # as such the following two updates ignore the splitted posts
            # completly and just set the highest id (== max recent posts) as
            # last_post.
            Forum.objects.filter(id__in=new_ids).update(
                last_post=Topic.objects.filter(forum__id__in=new_ids) \
                            .aggregate(count=Max('last_post'))['count'])

            Forum.objects.filter(id__in=old_ids).update(
                last_post=Topic.objects.filter(forum__id__in=old_ids) \
                            .aggregate(count=Max('last_post'))['count'])

            # Update post_count of the forums
            Forum.objects.filter(id__in=new_ids)\
                .update(post_count=F('post_count') + len(posts))
            Forum.objects.filter(id__in=old_ids)\
                .update(post_count=F('post_count') - len(posts))

        # update the search index which has the post --> topic mapping indexed
        Post.multi_update_search([post.id for post in posts])

        new_topic.forum.invalidate_topic_cache()
        old_topic.forum.invalidate_topic_cache()

    @property
    def grouped_attachments(self):
        def expr(v):
            if not v.mimetype.startswith('image') or v.mimetype not in SUPPORTED_IMAGE_TYPES:
                return u''
            return _(u'Pictures')

        if hasattr(self, '_attachments_cache'):
            attachments = sorted(self._attachments_cache, key=expr)
        else:
            attachments = sorted(self.attachments.all(), key=expr)

        grouped = [(x[0], list(x[1]), 'broken' if not x[0] else '') \
                   for x in groupby(attachments, expr)]
        return grouped

    def check_ownpost_limit(self, type='edit'):
        if type == 'edit':
            if self.topic.last_post_id == self.id:
                t = settings.FORUM_OWNPOST_EDIT_LIMIT[0]
            else:
                t = settings.FORUM_OWNPOST_EDIT_LIMIT[1]
        elif type == 'delete':
            if self.topic.last_post_id == self.id:
                t = settings.FORUM_OWNPOST_DELETE_LIMIT[0]
            else:
                t = settings.FORUM_OWNPOST_DELETE_LIMIT[1]
        else:
            raise KeyError("invalid type: choose one of (edit, delete)")

        if t == 0:
            return False
        if t == -1:
            return True
        delta = datetime.utcnow() - self.pub_date.replace(tzinfo=None)
        return timedelta_to_seconds(delta) < t

    def __unicode__(self):
        return '%s - %s' % (
            self.topic.title,
            self.text[0:20]
        )

    def __repr__(self):
        return '<%s id=%s author=%s>' % (
            self.__class__.__name__,
            self.id,
            self.author_id
        )


class Attachment(models.Model):
    """Represents an attachment associated to a post."""

    file = models.FileField(upload_to='forum/attachments/temp')
    name = models.CharField(max_length=255)
    comment = models.TextField(null=True, blank=True)
    mimetype = models.CharField(max_length=100, null=True)

    post = models.ForeignKey(Post, null=True, related_name='attachments')

    @staticmethod
    def create(name, uploaded_file, mime, attachments, override=False, **kwargs):
        """
        This method writes a new attachment bound to a post that is
        not written into the database yet.
        It either returns the new created attachment or None if another
        attachment with that name already exists (and `override` is False).

        :Parameters:
            name
                The file name of the attachment.
            uploaded_file
                The attachment.
            mime
                The mimetype of the attachment (guess_file is implemented
                as fallback)
            attachments
                A list that includes attachments that are
                already attached to this (not-yet-existing) post.
            override
                Specifies whether other attachments for the same post should
                be overwritten if they have the same name.
        """
        name = get_filename(name, uploaded_file)
        # check whether an attachment with the same name already exists
        existing = filter(lambda a: a.name == name, attachments)
        exists = bool(existing)
        if exists:
            existing = existing[0]

        if exists and override:
            attachments.remove(existing)
            existing.delete()
            exists = False

        if not exists:
            # create a temporary filename so we can identify the attachment
            # on binding to the posts
            fn = md5((str(time()) + name).encode('utf-8')).hexdigest()
            attachment = Attachment(name=name, mimetype=mime, **kwargs)
            attachment.file.save(fn, uploaded_file)
            return attachment

    def delete(self):
        """
        Delete the attachment from the filesystem and
        also mark the database-object for deleting.
        """
        self.file.delete(save=False)
        super(Attachment, self).delete()

    @staticmethod
    def update_post_ids(att_ids, post):
        """
        Update the post_id of a few unbound attachments.

        :param list att_ids: A list of the attachment's ids.
        :param Post post: The new post object.
        """
        if not att_ids or not post:
            return False

        attachments = Attachment.objects.filter(id__in=att_ids, post=None).all()

        base_path = datetime.utcnow().strftime('forum/attachments/%S/%W')

        for attachment in attachments:
            new_name = get_filename('%d-%s' % (post.pk, attachment.name))
            new_name = path.join(base_path, new_name)

            storage = attachment.file.storage
            new_name = storage.save(new_name, attachment.file)
            storage.delete(attachment.file.name)

            Attachment.objects.filter(pk=attachment.pk).update(file=new_name,
                post=post.pk)

    @property
    def size(self):
        """The size of the attachment in bytes."""
        f = self.file
        return f.size if f.storage.exists(f.name) else 0.0

    @property
    def contents(self):
        """
        The raw contents of the file.  This is usually unsafe because
        it can cause the memory limit to be reached if the file is too
        big.

        This method only opens files that are less than 1KB great, if the
        file is greater we return None.
        """
        f = self.file
        size = self.size
        if (size / 1024) > 1 or size == 0.0:
            return

        with f.file as fobj:
            return fobj.read()

    @property
    def html_representation(self):
        """
        This method returns a `HTML` representation of the attachment for the
        `show_action` page.  If this method does not know about an internal
        representation for the object the return value will be an download
        link to the raw attachment.
        """
        url = escape(self.get_absolute_url())
        show_thumbnails = current_request.user.settings.get(
            'show_thumbnails', False)
        show_preview = current_request.user.settings.get(
            'show_preview', False)

        def isimage():
            """
            This helper returns True if this attachment is a supported image,
            else False.
            """
            return True if self.mimetype in SUPPORTED_IMAGE_TYPES else False

        def istext():
            """
            This helper returns True if this attachment is a text file.
            """
            return self.mimetype.startswith('text/')

        def thumbnail():
            """
            This helper returns the thumbnail url of this attachment or None
            if there is no way to create a thumbnail.
            """
            ff = self.file.name.encode('utf-8')
            img_path = path.join(settings.MEDIA_ROOT,
                'forum/thumbnails/%s-%s' % (self.id, ff.split('/')[-1]))
            thumb = get_thumbnail(self.file.path.encode('utf-8'), img_path, *settings.FORUM_THUMBNAIL_SIZE)
            if thumb:
                return href('media', 'forum/thumbnails/%s' % thumb.split('/')[-1])
            return thumb

        if show_preview and show_thumbnails and isimage():
            thumb = thumbnail()
            if thumb:
                return format_html(u'<a href="{}"><img class="preview" src="{}" alt="{}" title="{}"></a>',
                                   url, thumb, self.comment, self.comment
                )
            else:
                linktext = pgettext('Link text to an image attachment',
                    u'View %(name)s') % {'name': self.name}
                return format_html(u'<a href="{}" type="{}" title="{}">{}</a>',
                                   url, self.mimetype, self.comment, linktext)
        elif show_preview and istext():
            contents = self.contents
            if contents is not None:
                try:
                    highlighted = highlight_code(force_unicode(contents), mimetype=self.mimetype)
                    return format_html(u'<div class="code">{}</div>', highlighted)
                except DjangoUnicodeDecodeError:
                    pass

        linktext = pgettext('Link text to download an attachment',
            u'Download %(name)s') % {'name': self.name}
        return format_html(u'<a href="{}" type="{}" title="{}">{}</a>',
                           url, self.mimetype, self.comment, linktext)

    def get_absolute_url(self, action=None):
        return self.file.url


class Privilege(models.Model):
    group = models.ForeignKey(Group, null=True)
    user = models.ForeignKey(User, null=True)
    forum = models.ForeignKey(Forum)
    positive = models.IntegerField(null=True, default=0)
    negative = models.IntegerField(null=True, default=0)

    def save(self, *args, **kwargs):
        # Check that the value is not a negative value as this
        # would raise nasty bugs in inyoka.forum.acl.  Change values
        # to positive integers everytime.
        # Additionally make `None` to be converted to 0
        for name in ('positive', 'negative'):
            value = getattr(self, name)
            value = value or 0
            setattr(self, name, abs(value))
        super(Privilege, self).save(*args, **kwargs)

    def __repr__(self):
        gid, uid = self.group_id, self.user_id
        return '<Privilege(id, %s, fid:%s, %s, %s)' % (
            (self.group_id and 'gid:%s' % gid or 'uid:%s' % uid,
             self.forum_id, self.positive, self.negative))


class PollOption(models.Model):
    poll = models.ForeignKey('forum.Poll', related_name='options')
    name = models.CharField(max_length=250)
    votes = models.IntegerField(default=0)

    @property
    def percentage(self):
        """Calculate the percentage of votes for this poll option."""
        if self.poll.votes:
            return self.votes / self.poll.votes * 100.0
        return 0.0


class PollVote(models.Model):
    voter = models.ForeignKey(User)
    poll = models.ForeignKey('forum.Poll', related_name='votings')

    class Meta:
        db_table = 'forum_voter'


class Poll(models.Model):
    question = models.CharField(max_length=250)
    start_time = models.DateTimeField(default=datetime.utcnow)
    end_time = models.DateTimeField(null=True)
    multiple_votes = models.BooleanField(default=False)

    topic = models.ForeignKey(Topic, null=True, db_index=True, related_name='polls')

    @deferred
    def votes(self):
        """Calculate the total number of votes in this poll."""
        return sum(o.votes for o in self.options.all())

    @property
    def participated(self):
        user = current_request.user
        return PollVote.objects.filter(poll=self, voter=user).exists()

    @property
    def ended(self):
        """Returns a boolean whether the poll ended already"""
        return self.end_time and datetime.utcnow() > self.end_time

    @deferred
    def can_vote(self):
        """
        Returns a boolean whether the current user can vote in this poll.
        """
        return not self.ended and not self.participated


class WelcomeMessage(models.Model):
    """This class can be used to attach additional welcome messages to
    a category or forum.

    That might be usefull for greeting users or to explain extra rules.
    The message will be displayed only once for each user.
    """

    title = models.CharField(max_length=120)
    text = models.TextField()
    rendered_text = models.TextField()

    def save(self, *args, **kwargs):
        self.rendered_text = self.render_text()
        super(WelcomeMessage, self).save(*args, **kwargs)

    def render_text(self, request=None, format='html'):
        if request is None:
            try:
                request = current_request._get_current_object()
            except RuntimeError:
                request = None
        context = RenderContext(request, simplified=True)
        return parse(self.text).render(context, format)


class ReadStatus(object):
    """
    Manages the read status of forums and topics for a specific user.
    """

    def __init__(self, serialized_data):
        self.data = cPickle.loads(str(serialized_data)) if serialized_data else {}

    def __call__(self, item):
        """
        Determine the read status for a forum or topic. If the topic
        was allready read by the user, True is returned.
        """
        forum_id, post_id = None, None
        is_forum = isinstance(item, Forum)
        if is_forum:
            forum_id, post_id = item.id, item.last_post_id
        elif isinstance(item, Topic):
            forum_id, post_id = item.forum_id, item.last_post_id
        else:
            raise ValueError('Can\'t determine read status of an unknown type')
        row = self.data.get(forum_id, (None, []))
        if row[0] >= post_id:
            return True
        elif is_forum:
            return False
        return post_id in row[1]

    def mark(self, item):
        """
        Mark a forum or topic as read. Note that you must save the database
        changes explicitely!
        """
        if self(item):
            return False
        forum_id = item.id if isinstance(item, Forum) else item.forum_id
        post_id = item.last_post.id

        if isinstance(item, Forum):
            self.data[forum_id] = (post_id, set())
            for child in item.children:
                self.mark(child)
            if item.parent_id:
                parents_children = item.parent.children
                unread_items = reduce(lambda a, b: a and b,
                                      [self(c) for c in parents_children], True)
                if parents_children and unread_items:
                    self.mark(item.parent)
            return True

        row = self.data.get(forum_id, (None, set()))
        row[1].add(post_id)
        children = item.forum.children
        if children:
            unread_children = reduce(lambda a, b: a and b,
                                     [self(c) for c in children], True)
            if unread_children:
                self.mark(item.forum)
                return True
        elif len(row[1]) > settings.FORUM_LIMIT_UNREAD:
            r = sorted(row[1])
            row = (r[settings.FORUM_LIMIT_UNREAD // 2],
                set(r[settings.FORUM_LIMIT_UNREAD // 2:]))
        self.data[forum_id] = row
        return True

    def serialize(self):
        return cPickle.dumps(self.data)


def mark_all_forums_read(user):
    """Shortcut to mark all forums as read to prevent serializing to often."""
    if user.is_anonymous:
        return
    for forum in Forum.objects.filter(parent=None):
        user._readstatus.mark(forum)
    user.forum_read_status = user._readstatus.serialize()
    user.save(update_fields=('forum_read_status',))


# Circular imports
