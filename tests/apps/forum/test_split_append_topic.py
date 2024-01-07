"""
    tests.apps.forum.test_split_append_topic
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test split function for topics that append posts to another thread.

    :copyright: (c) 2012-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.core.cache import cache

from inyoka.forum.models import Forum, Post, Topic
from inyoka.portal.user import User
from inyoka.utils.test import TestCase


class TestPostSplit(TestCase):
    """Test for splitting posts and appending them to an existing topic"""

    def setUp(self):
        super().setUp()
        self.user = User.objects.register_user('admin', 'admin', 'admin', False)

        self.category = Forum(name='category')
        self.category.save()
        self.forum1 = Forum(name='forum1')
        self.forum1.user_count_posts = True
        self.forum1.save()
        self.forum2 = Forum(name='forum2')
        self.forum2.user_count_posts = True
        self.forum2.save()

        self.topic1 = Topic(title='topic', author=self.user, forum=self.forum1)
        self.topic1.save()
        self.topic2 = Topic(title='topic2', author=self.user, forum=self.forum2)
        self.topic2.save()

        self.t1_posts = {}
        for i in range(10):
            self.t1_posts[i] = Post(text='post-1-%d' % i, author=self.user,
                    position=i, topic=self.topic1)
            self.t1_posts[i].save()

        self.t2_posts = {}
        for i in range(10):
            self.t2_posts[i] = Post(text='post-2-%d' % i, author=self.user,
                    position=i, topic=self.topic2)
            self.t2_posts[i].save()

    def _test_position(self, topic_id, postcount):
        vl = list(Post.objects.filter(topic_id=topic_id)
                      .values_list('position', flat=True).order_by('position'))
        self.assertEqual(vl, list(range(postcount)))

    def test_single_last_post(self):
        """Split the last post and append it"""
        t1 = Topic.objects.get(id=self.topic1.id)
        t2 = Topic.objects.get(id=self.topic2.id)

        Post.split((self.t1_posts[9],), t1, t2)

        cache.delete('forum/forums/%s' % self.forum1.slug)
        cache.delete('forum/forums/%s' % self.forum2.slug)
        t1 = Topic.objects.get(id=self.topic1.id)
        t2 = Topic.objects.get(id=self.topic2.id)
        f1 = Forum.objects.get(id=self.forum1.id)
        f2 = Forum.objects.get(id=self.forum2.id)

        self.assertEqual(t1.post_count.value(), 9)
        self.assertEqual(t2.post_count.value(), 11)

        self.assertEqual(t1.first_post_id, self.t1_posts[0].id)
        self.assertEqual(t2.first_post_id, self.t2_posts[0].id)

        self.assertEqual(t1.last_post_id, self.t1_posts[8].id)
        self.assertEqual(t2.last_post_id, self.t1_posts[9].id)

        self.assertEqual(f1.post_count.value(), 9)
        self.assertEqual(f2.post_count.value(), 11)

        self.assertEqual(f1.last_post_id, self.t1_posts[8].id)
        self.assertEqual(f2.last_post_id, self.t1_posts[9].id)

        post_ids = [p.id for k, p in list(self.t1_posts.items())][:-1]
        self.assertEqual([p.id for p in t1.posts.order_by('position')], post_ids)

        post_ids = [p.id for k, p in list(self.t2_posts.items())] + [self.t1_posts[9].id]
        self.assertEqual([p.id for p in t2.posts.order_by('position')], post_ids)

        self._test_position(t1, 9)
        self._test_position(t2, 11)

    def test_multiple_last_posts(self):
        """Split multiple consecutive last posts and append them"""
        t1 = Topic.objects.get(id=self.topic1.id)
        t2 = Topic.objects.get(id=self.topic2.id)

        Post.split((self.t1_posts[8], self.t1_posts[9]), t1, t2)

        cache.delete('forum/forums/%s' % self.forum1.slug)
        cache.delete('forum/forums/%s' % self.forum2.slug)
        t1 = Topic.objects.get(id=self.topic1.id)
        t2 = Topic.objects.get(id=self.topic2.id)
        f1 = Forum.objects.get(id=self.forum1.id)
        f2 = Forum.objects.get(id=self.forum2.id)

        self.assertEqual(t1.post_count.value(), 8)
        self.assertEqual(t2.post_count.value(), 12)

        self.assertEqual(t1.first_post_id, self.t1_posts[0].id)
        self.assertEqual(t2.first_post_id, self.t2_posts[0].id)

        self.assertEqual(t1.last_post_id, self.t1_posts[7].id)
        self.assertEqual(t2.last_post_id, self.t1_posts[9].id)

        self.assertEqual(f1.post_count.value(), 8)
        self.assertEqual(f2.post_count.value(), 12)

        self.assertEqual(f1.last_post_id, self.t1_posts[7].id)
        self.assertEqual(f2.last_post_id, self.t1_posts[9].id)

        post_ids = [p.id for k, p in list(self.t1_posts.items())][:-2]
        self.assertEqual([p.id for p in t1.posts.order_by('position')], post_ids)

        post_ids = [p.id for k, p in list(self.t2_posts.items())] + \
            [self.t1_posts[8].id, self.t1_posts[9].id]
        self.assertEqual([p.id for p in t2.posts.order_by('position')], post_ids)

        self._test_position(t1, 8)
        self._test_position(t2, 12)

    def test_single_middle_post(self):
        """Split a single middle post and append it"""
        t1 = Topic.objects.get(id=self.topic1.id)
        t2 = Topic.objects.get(id=self.topic2.id)

        Post.split((self.t1_posts[3],), t1, t2)

        cache.delete('forum/forums/%s' % self.forum1.slug)
        cache.delete('forum/forums/%s' % self.forum2.slug)
        t1 = Topic.objects.get(id=self.topic1.id)
        t2 = Topic.objects.get(id=self.topic2.id)
        f1 = Forum.objects.get(id=self.forum1.id)
        f2 = Forum.objects.get(id=self.forum2.id)

        self.assertEqual(t1.post_count.value(), 9)
        self.assertEqual(t2.post_count.value(), 11)

        self.assertEqual(t1.first_post_id, self.t1_posts[0].id)
        self.assertEqual(t2.first_post_id, self.t2_posts[0].id)

        self.assertEqual(t1.last_post_id, self.t1_posts[9].id)
        self.assertEqual(t2.last_post_id, self.t1_posts[3].id)

        self.assertEqual(f1.post_count.value(), 9)
        self.assertEqual(f2.post_count.value(), 11)

        self.assertEqual(f1.last_post_id, self.t1_posts[9].id)
        self.assertEqual(f2.last_post_id, self.t1_posts[3].id)

        ids = [p.id for k, p in list(self.t1_posts.items())]
        post_ids = ids[:3] + ids[4:]
        self.assertEqual([p.id for p in t1.posts.order_by('position')], post_ids)

        post_ids = [p.id for k, p in list(self.t2_posts.items())] + [self.t1_posts[3].id]
        self.assertEqual([p.id for p in t2.posts.order_by('position')], post_ids)

        self._test_position(t1, 9)
        self._test_position(t2, 11)

    def test_single_consecutive_middle_posts(self):
        """Split multiple consecutive posts from the middle and append them"""
        t1 = Topic.objects.get(id=self.topic1.id)
        t2 = Topic.objects.get(id=self.topic2.id)

        Post.split((self.t1_posts[5], self.t1_posts[6]), t1, t2)

        cache.delete('forum/forums/%s' % self.forum1.slug)
        cache.delete('forum/forums/%s' % self.forum2.slug)
        t1 = Topic.objects.get(id=self.topic1.id)
        t2 = Topic.objects.get(id=self.topic2.id)
        f1 = Forum.objects.get(id=self.forum1.id)
        f2 = Forum.objects.get(id=self.forum2.id)

        self.assertEqual(t1.post_count.value(), 8)
        self.assertEqual(t2.post_count.value(), 12)

        self.assertEqual(t1.first_post_id, self.t1_posts[0].id)
        self.assertEqual(t2.first_post_id, self.t2_posts[0].id)

        self.assertEqual(t1.last_post_id, self.t1_posts[9].id)
        self.assertEqual(t2.last_post_id, self.t1_posts[6].id)

        self.assertEqual(f1.post_count.value(), 8)
        self.assertEqual(f2.post_count.value(), 12)

        self.assertEqual(f1.last_post_id, self.t1_posts[9].id)
        self.assertEqual(f2.last_post_id, self.t1_posts[6].id)

        ids = [p.id for k, p in list(self.t1_posts.items())]
        post_ids = ids[:5] + ids[7:]
        self.assertEqual([p.id for p in t1.posts.order_by('position')], post_ids)

        post_ids = [p.id for k, p in list(self.t2_posts.items())] + \
                   [self.t1_posts[5].id, self.t1_posts[6].id]
        self.assertEqual([p.id for p in t2.posts.order_by('position')], post_ids)

        self._test_position(t1, 8)
        self._test_position(t2, 12)

    def test_multiple_middle_posts(self):
        """Split multiple single and non-consecutive posts from the middle
        and append them
        """
        t1 = Topic.objects.get(id=self.topic1.id)
        t2 = Topic.objects.get(id=self.topic2.id)

        Post.split((self.t1_posts[2], self.t1_posts[4], self.t1_posts[8]), t1, t2)

        cache.delete('forum/forums/%s' % self.forum1.slug)
        cache.delete('forum/forums/%s' % self.forum2.slug)
        t1 = Topic.objects.get(id=self.topic1.id)
        t2 = Topic.objects.get(id=self.topic2.id)
        f1 = Forum.objects.get(id=self.forum1.id)
        f2 = Forum.objects.get(id=self.forum2.id)

        self.assertEqual(t1.post_count.value(), 7)
        self.assertEqual(t2.post_count.value(), 13)

        self.assertEqual(t1.first_post_id, self.t1_posts[0].id)
        self.assertEqual(t2.first_post_id, self.t2_posts[0].id)

        self.assertEqual(t1.last_post_id, self.t1_posts[9].id)
        self.assertEqual(t2.last_post_id, self.t1_posts[8].id)

        self.assertEqual(f1.post_count.value(), 7)
        self.assertEqual(f2.post_count.value(), 13)

        self.assertEqual(f1.last_post_id, self.t1_posts[9].id)
        self.assertEqual(f2.last_post_id, self.t1_posts[8].id)

        ids = [p.id for k, p in list(self.t1_posts.items())]
        post_ids = ids[0:2] + ids[3:4] + ids[5:8] + ids[9:]
        self.assertEqual([p.id for p in t1.posts.order_by('position')], post_ids)

        post_ids = [p.id for k, p in list(self.t2_posts.items())] + \
                   [self.t1_posts[2].id, self.t1_posts[4].id, self.t1_posts[8].id]
        self.assertEqual([p.id for p in t2.posts.order_by('position')], post_ids)

        self._test_position(t1, 7)
        self._test_position(t2, 13)

    def test_multiple_consecutive_middle_posts(self):
        """Split groups of consecutives posts from the middle and append them"""
        t1 = Topic.objects.get(id=self.topic1.id)
        t2 = Topic.objects.get(id=self.topic2.id)

        Post.split((self.t1_posts[2], self.t1_posts[3], self.t1_posts[6],
                    self.t1_posts[7], self.t1_posts[8]), t1, t2)

        cache.delete('forum/forums/%s' % self.forum1.slug)
        cache.delete('forum/forums/%s' % self.forum2.slug)
        t1 = Topic.objects.get(id=self.topic1.id)
        t2 = Topic.objects.get(id=self.topic2.id)
        f1 = Forum.objects.get(id=self.forum1.id)
        f2 = Forum.objects.get(id=self.forum2.id)

        self.assertEqual(t1.post_count.value(), 5)
        self.assertEqual(t2.post_count.value(), 15)

        self.assertEqual(t1.first_post_id, self.t1_posts[0].id)
        self.assertEqual(t2.first_post_id, self.t2_posts[0].id)

        self.assertEqual(t1.last_post_id, self.t1_posts[9].id)
        self.assertEqual(t2.last_post_id, self.t1_posts[8].id)

        self.assertEqual(f1.post_count.value(), 5)
        self.assertEqual(f2.post_count.value(), 15)

        self.assertEqual(f1.last_post_id, self.t1_posts[9].id)
        self.assertEqual(f2.last_post_id, self.t1_posts[8].id)

        ids = [p.id for k, p in list(self.t1_posts.items())]
        post_ids = ids[0:2] + ids[4:6] + ids[9:]
        self.assertEqual([p.id for p in t1.posts.order_by('position')], post_ids)

        post_ids = ([p.id for k, p in list(self.t2_posts.items())] +
                    ids[2:4] + ids[6:9])
        self.assertEqual([p.id for p in t2.posts.order_by('position')], post_ids)

        self._test_position(t1, 5)
        self._test_position(t2, 15)
