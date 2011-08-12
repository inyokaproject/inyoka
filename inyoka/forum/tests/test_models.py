#-*- coding: utf-8 -*-
from django.db import connection
from django.core.cache import cache
from django.test import TestCase, TransactionTestCase
from django.conf import settings

from inyoka.forum.models import Forum, Topic, Post
from inyoka.portal.user import User
from inyoka.utils.cache import request_cache


class TestForumModel(TestCase):

    def setUp(self):
        self.parent1 = Forum(name='This is a test')
        self.parent1.save()
        self.parent2 = Forum(name='This is a second test', parent=self.parent1)
        self.parent2.save()
        self.forum = Forum(name='This rocks damnit', parent=self.parent2)
        self.forum.save()

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
        self.assertEqual(Forum.objects.get_all_forums_cached(), map)
        self.assertEqual(cache.get('forum/forums/this-is-a-test'), self.parent1)
        new_forum = Forum(name='yeha')
        new_forum.save()
        new_map = map.copy()
        new_map.update({'forum/forums/yeha': new_forum})
        self.assertEqual(cache.get('forum/forums/yeha'), None)
        self.assertEqual(Forum.objects.get_all_forums_cached(), new_map)
        self.assertEqual(cache.get('forum/forums/yeha'), new_forum)


class TestPostSplit(TransactionTestCase):

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

        self.fp1 = Post(text=u'test1', author=self.user)
        self.topic1.posts.add(self.fp1)
        self.topic1.posts.add(Post(text=u'test2', author=self.user))
        self.lp1 = Post(text=u'test3', author=self.user)
        self.topic1.posts.add(self.lp1)
        self.fp2 = Post(text=u'test4', author=self.user)
        self.topic2.posts.add(self.fp2)

    def test_post_counter(self):
        user = User.objects.get(id=self.user.id)
        self.assertEqual(user.post_count, 3)

    def test_topic_count(self):
        self.assertEqual(Topic.objects.get(id=self.topic1.id).post_count, 3)
        self.assertEqual(Topic.objects.get(id=self.topic2.id).post_count, 1)

    def test_topic_first_post(self):
        self.assertEqual(Topic.objects.get(id=self.topic1.id).first_post,
                         Post.objects.get(id=self.fp1.id))

    def test_topic_last_post(self):
        self.assertEqual(Topic.objects.get(id=self.topic1.id).last_post,
                         Post.objects.get(id=self.lp1.id))

    def test_split_post(self):
        posts = Post.objects.filter(text__in=(u'test2', u'test3')).all()

        t1 = Topic.objects.get(id=self.topic1.id)
        t2 = Topic.objects.get(id=self.topic2.id)
        Post.split(posts, t1, t2)
        user = User.objects.get(id=self.user.id)
        t1 = Topic.objects.get(id=self.topic1.id)
        t2 = Topic.objects.get(id=self.topic2.id)

        self.assertEqual(user.post_count, 1)
        self.assertEqual(t1.post_count, 1)
        self.assertEqual(t2.post_count, 3)
        self.assertEqual(t1.first_post, self.fp1)
        self.assertEqual(t2.first_post, self.fp2)
        self.assertEqual(t1.last_post, self.fp1)
        self.assertEqual(t2.last_post, Post.objects.get(text='test3'))
        post_ids = [p.pk for p in [self.fp2] + list(posts)]
        self.assertEqual([p.pk for p in t2.posts.order_by('position')], post_ids)

    def test_split_new_topic(self):
        posts = Post.objects.filter(text__in=(u'test2', u'test3')).all()
        new_topic = Topic(title='topic', author=self.user)
        self.forum2.topics.add(new_topic)

        t1 = Topic.objects.get(id=self.topic1.id)

        Post.split(posts, t1, new_topic)

        user = User.objects.get(id=self.user.id)
        t1 = Topic.objects.get(id=self.topic1.id)
        t2 = Topic.objects.get(id=new_topic.id)

        self.assertEqual(user.post_count, 1)
        self.assertEqual(t1.post_count, 1)
        self.assertEqual(t2.post_count, 2)
        self.assertEqual(t1.first_post, self.fp1)
        self.assertEqual(t2.first_post, Post.objects.get(text='test2'))
        self.assertEqual(t1.last_post, self.fp1)
        self.assertEqual(t1.forum.last_post, self.lp1)
        self.assertEqual(t2.last_post, Post.objects.get(text='test3'))
        self.assertEqual(t2.forum.last_post, self.fp2)
        post_ids = [p.pk for p in list(posts)]
        self.assertEqual([p.pk for p in t2.posts.order_by('position')], post_ids)

    def test_split_post_remove_topic(self):
        posts = Post.objects.filter(text__in=(u'test1', u'test2', u'test3')).all()
        Post.split(posts, self.topic1, self.topic2)
        user = User.objects.get(id=self.user.id)
        t2 = Topic.objects.get(id=self.topic2.id)

        self.assertEqual(user.post_count, 0)
        self.assertEqual(Topic.objects.filter(id=self.topic1.id).count(), 0)
        self.assertEqual(t2.post_count, 4)
        self.assertEqual(t2.first_post, self.fp2)
        self.assertEqual(t2.last_post, Post.objects.get(text='test3'))
        post_ids = [p.pk for p in [self.fp2] + list(posts)]
        self.assertEqual([p.pk for p in t2.posts.order_by('position')], post_ids)


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
        self.topic1.posts.add(Post(text=u'test3', author=self.user))
        self.topic2.posts.add(Post(text=u'test4', author=self.user))

    def test_post_counter(self):
        user = User.objects.get(id=self.user.id)
        self.assertEqual(user.post_count, 3)

    def test_topic_count(self):
        self.assertEqual(Topic.objects.get(id=self.topic1.id).post_count, 3)
        self.assertEqual(Topic.objects.get(id=self.topic2.id).post_count, 1)

    def test_topic_move(self):
        Topic.objects.get(id=self.topic1.id).move(self.forum2)
        user = User.objects.get(id=self.user.id)
        self.assertEqual(user.post_count, 0)
        self.assertEqual(Topic.objects.get(id=self.topic1.id).post_count, 3)
