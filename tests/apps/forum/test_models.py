#-*- coding: utf-8 -*-
"""
    tests.apps.forum.test_models
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test forum models.

    :copyright: (c) 2011-2013 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL.
"""
from django.conf import settings
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.test import TestCase
from django.test.utils import override_settings

from inyoka.forum.models import Post, Topic, Forum, Attachment
from inyoka.portal.user import User
from inyoka.utils.cache import request_cache


class TestAttachmentModel(TestCase):
    def test_regression_ticket760(self):
        a = Attachment.create('test.txt', ContentFile('test'), 'text/plain', [])
        try:
            self.assertEqual(a.contents, 'test')
        finally:
            a.delete()  # Yank the file from the filesystem


class TestForumModel(TestCase):

    def setUp(self):
        self.parent1 = Forum(name='This is a test')
        self.parent1.save()
        self.parent2 = Forum(name='This is a second test', parent=self.parent1)
        self.parent2.save()
        self.forum = Forum(name='This rocks damnit', parent=self.parent2)
        self.forum.save()

        request_cache.clear()

    def tearDown(self):
        request_cache.clear()

    def test_automatic_slug(self):
        self.assertEqual(self.forum.slug, 'this-rocks-damnit')

    def test_parents(self):
        self.assertEqual(self.parent1.parents, [])
        self.assertEqual(self.parent2.parents, [self.parent1])
        self.assertEqual(self.forum.parents, [self.parent2, self.parent1])

    def test_children(self):
        self.assertEqual(self.forum.children, [])
        self.assertEqual(self.parent2.children, [self.forum])
        self.assertEqual(self.parent1.children, [self.parent2])

    def test_get_children_recursive(self):
        rec = list(Forum.get_children_recursive((self.forum, self.parent1, self.parent2)))
        rec2 = list(Forum.get_children_recursive((self.forum,)))
        rec3 = list(Forum.get_children_recursive((self.parent2,)))
        rec4 = list(Forum.get_children_recursive((self.parent2,), self.parent1))
        self.assertEqual(rec, [(0, self.parent1), (1, self.parent2), (2, self.forum)])
        self.assertEqual(rec2, [])
        self.assertEqual(rec3, [])
        self.assertEqual(rec4, [(0, self.parent2)])

    def test_get_slugs(self):
        map = {self.parent1.id: 'this-is-a-test',
               self.parent2.id: 'this-is-a-second-test',
               self.forum.id: 'this-rocks-damnit'}
        request_cache.delete('forum/slugs')
        self.assertEqual(request_cache.get('forum/slugs'), None)
        self.assertEqual(Forum.objects.get_slugs(), map)
        self.assertEqual(request_cache.get('forum/slugs'), map)

    def test_get_ids(self):
        self.assertEqual(set(Forum.objects.get_ids()),
                         set([self.parent1.id, self.parent2.id, self.forum.id]))

    def test_unified_get(self):
        cache.delete('forum/forums/%s' % self.forum.slug)
        self.assertEqual(self.forum, Forum.objects.get(self.forum.id))
        self.assertEqual(cache.get('forum/forums/%s' % self.forum.slug), self.forum)

        self.assertEqual(self.forum, Forum.objects.get(self.forum.slug))
        self.assertEqual(self.forum, Forum.objects.get(id=self.forum.id))
        self.assertEqual(self.forum, Forum.objects.get(slug=self.forum.slug))

    def test_get_all_forums_cached(self):
        map = {'forum/forums/this-is-a-test': self.parent1,
               'forum/forums/this-is-a-second-test': self.parent2,
               'forum/forums/this-rocks-damnit': self.forum}
        cache.delete_many(map.keys())
        request_cache.delete('forum/slugs')
        self.assertEqual(Forum.objects.get_all_forums_cached(), map)
        self.assertEqual(cache.get('forum/forums/this-is-a-test'), self.parent1)
        new_forum = Forum(name='yeha')
        new_forum.save()
        new_map = map.copy()
        new_map.update({'forum/forums/yeha': new_forum})
        self.assertEqual(cache.get('forum/forums/yeha'), None)
        self.assertEqual(Forum.objects.get_all_forums_cached(), new_map)
        self.assertEqual(cache.get('forum/forums/yeha'), new_forum)
        new_forum.delete()

    def test_post_count(self):
        user = User.objects.register_user('admin', 'admin', 'admin', False)
        t1 = Topic(title='topic', author=user)
        t2 = Topic(title='topic2', author=user)

        self.parent2.topics.add(t1)
        self.forum.topics.add(t2)

        for i in xrange(5):
            t1.posts.add(Post(text='post%d t1' % i,
                author=user, position=i))
            t2.posts.add(Post(text='post%d t2' % i,
                author=user, position=i))

        cache.delete('forum/forums/%s' % self.parent1.slug)
        f = Forum.objects.get(id=self.parent1.id)
        self.assertEqual(f.post_count, 10)

        cache.delete('forum/forums/%s' % self.parent2.slug)
        f = Forum.objects.get(id=self.parent2.id)
        self.assertEqual(f.post_count, 10)

        cache.delete('forum/forums/%s' % self.forum.slug)
        f = Forum.objects.get(id=self.forum.id)
        self.assertEqual(f.post_count, 5)

    def test_get_absolute_url(self):
        url1 = self.forum.get_absolute_url('show', foo='val1', bar='val2')
        url1_target = ''.join(['http://forum.', settings.BASE_DOMAIN_NAME,
                                       '/forum/', self.forum.slug, '/',
                                       '?foo=val1&bar=val2'])
        self.assertEqual(url1, url1_target)


class TestPostModel(TestCase):

    def setUp(self):
        self.user = User.objects.register_user('admin', 'admin', 'admin', False)

        self.category = Forum(name='category')
        self.category.save()
        self.forum = Forum(name='forum')
        self.forum.save()
        self.topic = Topic(title='topic', author=self.user)
        self.forum.topics.add(self.topic)

    @override_settings(BASE_DOMAIN_NAME='inyoka.local')
    def test_url_for_post(self):
        post = Post(text=u'test1', author=self.user)
        self.topic.posts.add(post)
        self.assertEqual(Post.url_for_post(post.pk),
                         'http://forum.inyoka.local/topic/topic/#post-%s' % post.pk)

    @override_settings(BASE_DOMAIN_NAME='inyoka.local')
    def test_url_for_post_multiple_pages(self):
        posts = []
        for idx in xrange(45):
            post = Post(text=u'test%s' % idx, author=self.user)
            self.topic.posts.add(post)
            posts.append(post.pk)
        self.assertEqual(Post.url_for_post(posts[-1]),
                         'http://forum.inyoka.local/topic/topic/4/#post-%s' % post.pk)

    def test_url_for_post_not_existing_post(self):
        self.assertRaises(Post.DoesNotExist, Post.url_for_post, 250000913)


class TestPostSplit(TestCase):

    def setUp(self):
        self.user = User.objects.register_user('admin', 'admin', 'admin', False)

        self.category = Forum(name='category')
        self.category.save()
        self.forum1 = Forum(name='forum1')
        self.forum1.user_count_posts = True
        self.forum1.save()
        self.forum2 = Forum(name='forum2')
        self.forum2.user_count_posts = True
        self.forum2.save()

        self.topic1 = Topic(title='topic', author=self.user)
        self.topic2 = Topic(title='topic2', author=self.user)

        self.forum1.topics.add(self.topic1)
        self.forum2.topics.add(self.topic2)

        self.t1_posts = {}
        for i in xrange(5):
            self.t1_posts[i] = Post(text=u'post-1-%d' % i, author=self.user,
                    position=i)
            self.topic1.posts.add(self.t1_posts[i])

        self.t2_posts = {}
        for i in xrange(5):
            self.t2_posts[i] = Post(text=u'post-1-%d' % i, author=self.user,
                    position=i)
            self.topic2.posts.add(self.t2_posts[i])

    def test_post_counter(self):
        user = User.objects.get(id=self.user.id)
        self.assertEqual(user.post_count, 10)

    def test_topic_count(self):
        self.assertEqual(Topic.objects.get(id=self.topic1.id).post_count, 5)
        self.assertEqual(Topic.objects.get(id=self.topic2.id).post_count, 5)

    def test_topic_first_post(self):
        self.assertEqual(Topic.objects.get(id=self.topic1.id).first_post,
                         Post.objects.get(id=self.t1_posts[0].id))
        self.assertEqual(Topic.objects.get(id=self.topic2.id).first_post,
                         Post.objects.get(id=self.t2_posts[0].id))

    def test_topic_last_post(self):
        self.assertEqual(Topic.objects.get(id=self.topic1.id).last_post,
                         Post.objects.get(id=self.t1_posts[4].id))
        self.assertEqual(Topic.objects.get(id=self.topic2.id).last_post,
                         Post.objects.get(id=self.t2_posts[4].id))

    def test_split_renumber_old_positions(self):
        topic = Topic(title='positions', author=self.user)
        self.forum1.topics.add(topic)
        for i in range(5):
            topic.posts.add(Post(text='test', author=self.user, position=i))

        posts = Post.objects.filter(topic=topic, position__in=[1, 2, 4])

        Post.split(posts, topic, self.topic2)

        old_positions = Post.objects.filter(topic=topic).order_by('position')\
            .values_list('position', flat=True)
        self.assertEqual(list(old_positions), [0, 1])

    def test_split_post_remove_topic(self):
        Post.split(self.t1_posts.values(), self.topic1, self.topic2)
        cache.delete('forum/forums/%s' % self.forum1.slug)
        cache.delete('forum/forums/%s' % self.forum2.slug)
        t2 = Topic.objects.get(id=self.topic2.id)

        self.assertFalse(Topic.objects.filter(id=self.topic1.id).exists())
        self.assertEqual(t2.post_count, 10)
        self.assertEqual(t2.first_post.id, self.t2_posts[0].id)
        self.assertEqual(t2.last_post.id, self.t1_posts[4].id)
        post_ids = [p.id for k, p in self.t2_posts.items()] + \
                   [p.id for k, p in self.t1_posts.items()]
        self.assertEqual([p.id for p in t2.posts.order_by('position')], post_ids)


class TestPostMove(TestCase):

    def setUp(self):
        self.user = User.objects.register_user('admin', 'admin', 'admin', False)

        self.category = Forum(name='category')
        self.category.save()
        self.forum = Forum(name='forum')
        self.forum.user_count_posts = True
        self.forum.save()
        self.forum2 = Forum(name='forum2')
        self.forum2.user_count_posts = False
        self.forum2.save()
        self.topic1 = Topic(title='topic', author=self.user)
        self.forum.topics.add(self.topic1)
        self.topic2 = Topic(title='topic2', author=self.user)
        self.forum2.topics.add(self.topic2)

        self.topic1.posts.add(Post(text=u'test1', author=self.user))
        self.topic1.posts.add(Post(text=u'test2', author=self.user))
        self.lp1 = Post(text=u'test3', author=self.user)
        self.topic1.posts.add(self.lp1)
        self.lp2 = Post(text=u'test4', author=self.user)
        self.topic2.posts.add(self.lp2)

    def test_post_counter(self):
        user = User.objects.get(id=self.user.id)
        self.assertEqual(user.post_count, 3)

    def test_topic_count(self):
        self.assertEqual(Topic.objects.get(id=self.topic1.id).post_count, 3)
        self.assertEqual(Topic.objects.get(id=self.topic2.id).post_count, 1)

    def test_topic_move(self):
        Topic.objects.get(id=self.topic1.id).move(self.forum2)
        user = User.objects.get(id=self.user.id)
        topic = Topic.objects.get(id=self.topic1.id)
        self.assertEqual(user.post_count, 0)
        self.assertEqual(topic.post_count, 3)
        self.assertEqual(topic.last_post, self.lp1)
        self.assertEqual(topic.forum.last_post, self.lp2)
        self.assertEqual(Forum.objects.get(id=self.forum.id).last_post, None)


class PostDeletionTest(TestCase):

    def setUp(self):
        self.user = User.objects.register_user('admin', 'admin', 'admin', False)
        self.category = Forum.objects.create(name='category')
        self.parent = Forum.objects.create(name='parent', parent=self.category)
        self.forum = Forum.objects.create(name='forum', parent=self.parent)
        self.topic = Topic.objects.create(forum=self.forum, title='test',
                                     author=self.user)

        self.p1 = Post.objects.create(text='', author=self.user, topic=self.topic, position=0)
        self.p2 = Post.objects.create(text='', author=self.user, topic=self.topic)
        self.p3 = Post.objects.create(text='', author=self.user, topic=self.topic)
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_post_delete_at_end(self):
        # Warm up cache
        forum_cache_keys = Forum.objects.get_all_forums_cached().keys()
        data = cache.get_many(forum_cache_keys)
        self.assertEqual(data['forum/forums/category'].last_post_id, self.p3.pk)
        self.assertEqual(data['forum/forums/parent'].last_post_id, self.p3.pk)
        self.assertEqual(data['forum/forums/forum'].last_post_id, self.p3.pk)

        # trigger post deletion
        Post.objects.get(pk=self.p3.pk).delete()
        # ensure cache is properly pruned
        data = cache.get_many(forum_cache_keys)
        self.assertEqual(data, {})

        # last post got changed
        topic = Topic.objects.get(pk=self.topic.pk)
        self.assertEqual(topic.last_post_id, self.p2.pk)

        # forum.last_post is correct
        forums = [f for f in topic.forum.parents + [topic.forum] if f.last_post]
        last_post_ids = [f.last_post_id for f in forums]
        self.assertEqual(last_post_ids, [self.p2.pk, self.p2.pk, self.p2.pk])

        # refresh cache, check for proper last_post_id
        Forum.objects.get_all_forums_cached()
        data = cache.get_many(forum_cache_keys)
        self.assertEqual(data['forum/forums/category'].last_post_id, self.p2.pk)
        self.assertEqual(data['forum/forums/parent'].last_post_id, self.p2.pk)
        self.assertEqual(data['forum/forums/forum'].last_post_id, self.p2.pk)

    def test_post_delete_at_center(self):
        # last post wasn't changed
        topic = Topic.objects.get(pk=self.topic.pk)

        # trigger post deletion
        Post.objects.get(pk=self.p2.pk).delete()
        self.assertEqual(topic.last_post_id, self.p3.pk)
        # postions are still correct
        p1 = Post.objects.get(pk=self.p1.pk)
        self.assertEqual(p1.position, 0)
        p1 = Post.objects.get(pk=self.p3.pk)
        self.assertEqual(p1.position, 1)
        # forum.last_post is correct
        forums = [f for f in topic.forum.parents + [topic.forum] if f.last_post]
        last_post_ids = [f.last_post_id for f in forums]
        self.assertEqual(last_post_ids, [self.p3.pk, self.p3.pk, self.p3.pk])
