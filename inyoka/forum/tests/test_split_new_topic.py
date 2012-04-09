#-*- coding: utf-8 -*-
from django.core.cache import cache
from django.test import TestCase

from inyoka.forum.models import Forum, Topic, Post
from inyoka.portal.user import User
from inyoka.utils.cache import request_cache


class TestPostSplitNewTopic(TestCase):

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

        self.forum1.topics.add(self.topic1)

        self.t1_posts = {}
        for i in xrange(10):
            self.t1_posts[i] = Post(text=u'post-1-%d' % i, author=self.user,
                    position=i)
            self.topic1.posts.add(self.t1_posts[i])

    def test_single_last_post(self):
        t1 = Topic.objects.get(id=self.topic1.id)
        t2 = Topic(title='new topic', author=self.user)
        self.forum2.topics.add(t2)
        t2_id = t2.id

        Post.split((self.t1_posts[9],), t1, t2)

        cache.delete('forum/forums/%s' % self.forum1.slug)
        cache.delete('forum/forums/%s' % self.forum2.slug)
        t1 = Topic.objects.get(id=self.topic1.id)
        t2 = Topic.objects.get(id=t2_id)
        f1 = Forum.objects.get(id=self.forum1.id)
        f2 = Forum.objects.get(id=self.forum2.id)

        self.assertEqual(t1.post_count, 9)
        self.assertEqual(t2.post_count, 1)

        self.assertEqual(t1.first_post_id, self.t1_posts[0].id)
        self.assertEqual(t2.first_post_id, self.t1_posts[9].id)

        self.assertEqual(t1.last_post_id, self.t1_posts[8].id)
        self.assertEqual(t2.last_post_id, self.t1_posts[9].id)

        self.assertEqual(f1.post_count, 9)
        self.assertEqual(f2.post_count, 1)

        self.assertEqual(f1.last_post_id, self.t1_posts[8].id)
        self.assertEqual(f2.last_post_id, self.t1_posts[9].id)

        post_ids = [p.id for k,p in self.t1_posts.items()][:-1]
        self.assertEqual([p.id for p in t1.posts.order_by('position')], post_ids)

        post_ids = [self.t1_posts[9].id]
        self.assertEqual([p.id for p in t2.posts.order_by('position')], post_ids)

    def test_multiple_last_posts(self):
        t1 = Topic.objects.get(id=self.topic1.id)
        t2 = Topic(title='new topic', author=self.user)
        self.forum2.topics.add(t2)
        t2_id = t2.id

        Post.split((self.t1_posts[8], self.t1_posts[9]), t1, t2)

        cache.delete('forum/forums/%s' % self.forum1.slug)
        cache.delete('forum/forums/%s' % self.forum2.slug)
        t1 = Topic.objects.get(id=self.topic1.id)
        t2 = Topic.objects.get(id=t2_id)
        f1 = Forum.objects.get(id=self.forum1.id)
        f2 = Forum.objects.get(id=self.forum2.id)

        self.assertEqual(t1.post_count, 8)
        self.assertEqual(t2.post_count, 2)

        self.assertEqual(t1.first_post_id, self.t1_posts[0].id)
        self.assertEqual(t2.first_post_id, self.t1_posts[8].id)

        self.assertEqual(t1.last_post_id, self.t1_posts[7].id)
        self.assertEqual(t2.last_post_id, self.t1_posts[9].id)

        self.assertEqual(f1.post_count, 8)
        self.assertEqual(f2.post_count, 2)

        self.assertEqual(f1.last_post_id, self.t1_posts[7].id)
        self.assertEqual(f2.last_post_id, self.t1_posts[9].id)

        post_ids = [p.id for k,p in self.t1_posts.items()][:-2]
        self.assertEqual([p.id for p in t1.posts.order_by('position')], post_ids)

        post_ids = [self.t1_posts[8].id, self.t1_posts[9].id]
        self.assertEqual([p.id for p in t2.posts.order_by('position')], post_ids)

    def test_single_middle_post(self):
        t1 = Topic.objects.get(id=self.topic1.id)
        t2 = Topic(title='new topic', author=self.user)
        self.forum2.topics.add(t2)
        t2_id = t2.id

        Post.split((self.t1_posts[3],), t1, t2)

        cache.delete('forum/forums/%s' % self.forum1.slug)
        cache.delete('forum/forums/%s' % self.forum2.slug)
        t1 = Topic.objects.get(id=self.topic1.id)
        t2 = Topic.objects.get(id=t2_id)
        f1 = Forum.objects.get(id=self.forum1.id)
        f2 = Forum.objects.get(id=self.forum2.id)

        self.assertEqual(t1.post_count, 9)
        self.assertEqual(t2.post_count, 1)

        self.assertEqual(t1.first_post_id, self.t1_posts[0].id)
        self.assertEqual(t2.first_post_id, self.t1_posts[3].id)

        self.assertEqual(t1.last_post_id, self.t1_posts[9].id)
        self.assertEqual(t2.last_post_id, self.t1_posts[3].id)

        self.assertEqual(f1.post_count, 9)
        self.assertEqual(f2.post_count, 1)

        self.assertEqual(f1.last_post_id, self.t1_posts[9].id)
        self.assertEqual(f2.last_post_id, self.t1_posts[3].id)

        ids = [p.id for k,p in self.t1_posts.items()]
        post_ids = ids[:3] + ids[4:]
        self.assertEqual([p.id for p in t1.posts.order_by('position')], post_ids)

        post_ids = [self.t1_posts[3].id]
        self.assertEqual([p.id for p in t2.posts.order_by('position')], post_ids)

    def test_single_consecutive_middle_posts(self):
        t1 = Topic.objects.get(id=self.topic1.id)
        t2 = Topic(title='new topic', author=self.user)
        self.forum2.topics.add(t2)
        t2_id = t2.id

        Post.split((self.t1_posts[5], self.t1_posts[6]), t1, t2)

        cache.delete('forum/forums/%s' % self.forum1.slug)
        cache.delete('forum/forums/%s' % self.forum2.slug)
        t1 = Topic.objects.get(id=self.topic1.id)
        t2 = Topic.objects.get(id=t2_id)
        f1 = Forum.objects.get(id=self.forum1.id)
        f2 = Forum.objects.get(id=self.forum2.id)

        self.assertEqual(t1.post_count, 8)
        self.assertEqual(t2.post_count, 2)

        self.assertEqual(t1.first_post_id, self.t1_posts[0].id)
        self.assertEqual(t2.first_post_id, self.t1_posts[5].id)

        self.assertEqual(t1.last_post_id, self.t1_posts[9].id)
        self.assertEqual(t2.last_post_id, self.t1_posts[6].id)

        self.assertEqual(f1.post_count, 8)
        self.assertEqual(f2.post_count, 2)

        self.assertEqual(f1.last_post_id, self.t1_posts[9].id)
        self.assertEqual(f2.last_post_id, self.t1_posts[6].id)

        ids = [p.id for k,p in self.t1_posts.items()]
        post_ids = ids[:5] + ids[7:]
        self.assertEqual([p.id for p in t1.posts.order_by('position')], post_ids)

        post_ids = [self.t1_posts[5].id, self.t1_posts[6].id]
        self.assertEqual([p.id for p in t2.posts.order_by('position')], post_ids)

    def test_multiple_middle_posts(self):
        t1 = Topic.objects.get(id=self.topic1.id)
        t2 = Topic(title='new topic', author=self.user)
        self.forum2.topics.add(t2)
        t2_id = t2.id

        Post.split((self.t1_posts[2],self.t1_posts[4],self.t1_posts[8]), t1, t2)

        cache.delete('forum/forums/%s' % self.forum1.slug)
        cache.delete('forum/forums/%s' % self.forum2.slug)
        t1 = Topic.objects.get(id=self.topic1.id)
        t2 = Topic.objects.get(id=t2_id)
        f1 = Forum.objects.get(id=self.forum1.id)
        f2 = Forum.objects.get(id=self.forum2.id)

        self.assertEqual(t1.post_count, 7)
        self.assertEqual(t2.post_count, 3)

        self.assertEqual(t1.first_post_id, self.t1_posts[0].id)
        self.assertEqual(t2.first_post_id, self.t1_posts[2].id)

        self.assertEqual(t1.last_post_id, self.t1_posts[9].id)
        self.assertEqual(t2.last_post_id, self.t1_posts[8].id)

        self.assertEqual(f1.post_count, 7)
        self.assertEqual(f2.post_count, 3)

        self.assertEqual(f1.last_post_id, self.t1_posts[9].id)
        self.assertEqual(f2.last_post_id, self.t1_posts[8].id)

        ids = [p.id for k,p in self.t1_posts.items()]
        post_ids = ids[0:2] + ids[3:4] + ids[5:8] + ids[9:]
        self.assertEqual([p.id for p in t1.posts.order_by('position')], post_ids)

        post_ids = [self.t1_posts[2].id, self.t1_posts[4].id, self.t1_posts[8].id]
        self.assertEqual([p.id for p in t2.posts.order_by('position')], post_ids)

    def test_multiple_consecutive_middle_posts(self):
        t1 = Topic.objects.get(id=self.topic1.id)
        t2 = Topic(title='new topic', author=self.user)
        self.forum2.topics.add(t2)
        t2_id = t2.id

        Post.split((self.t1_posts[2], self.t1_posts[3], self.t1_posts[6],
                    self.t1_posts[7], self.t1_posts[8]), t1, t2)

        cache.delete('forum/forums/%s' % self.forum1.slug)
        cache.delete('forum/forums/%s' % self.forum2.slug)
        t1 = Topic.objects.get(id=self.topic1.id)
        t2 = Topic.objects.get(id=t2_id)
        f1 = Forum.objects.get(id=self.forum1.id)
        f2 = Forum.objects.get(id=self.forum2.id)

        self.assertEqual(t1.post_count, 5)
        self.assertEqual(t2.post_count, 5)

        self.assertEqual(t1.first_post_id, self.t1_posts[0].id)
        self.assertEqual(t2.first_post_id, self.t1_posts[2].id)

        self.assertEqual(t1.last_post_id, self.t1_posts[9].id)
        self.assertEqual(t2.last_post_id, self.t1_posts[8].id)

        self.assertEqual(f1.post_count, 5)
        self.assertEqual(f2.post_count, 5)

        self.assertEqual(f1.last_post_id, self.t1_posts[9].id)
        self.assertEqual(f2.last_post_id, self.t1_posts[8].id)

        ids = [p.id for k,p in self.t1_posts.items()]
        post_ids = ids[0:2] + ids[4:6] + ids[9:]
        self.assertEqual([p.id for p in t1.posts.order_by('position')], post_ids)

        post_ids = ids[2:4] + ids[6:9]
        self.assertEqual([p.id for p in t2.posts.order_by('position')], post_ids)

    """
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
    """
