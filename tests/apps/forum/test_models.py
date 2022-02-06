# -*- coding: utf-8 -*-
"""
    tests.apps.forum.test_models
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test forum models.

    :copyright: (c) 2011-2022 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.conf import settings
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.test.utils import override_settings
from mock import patch

from inyoka.forum.models import Attachment, Forum, Post, PostRevision, Topic
from inyoka.utils.test import TestCase
from tests.apps.forum.forum_test_class import ForumTestCase, ForumTestCaseWithSecondItems


class TestAttachmentModel(TestCase):
    def test_regression_ticket760(self):
        a = Attachment.create('test.txt', ContentFile('test'), 'text/plain', [])
        try:
            self.assertEqual(a.contents, b'test')
        finally:
            a.delete()  # Yank the file from the filesystem


class TestForumModel(ForumTestCase):

    def test_automatic_slug(self):
        self.assertEqual(self.forum.slug, 'forum')

    def test_parents(self):
        self.assertEqual(self.category.parents, [])
        self.assertEqual(self.parent.parents, [self.category])
        self.assertEqual(self.forum.parents, [self.parent, self.category])

    def test_is_category(self):
        self.assertEqual(self.category.is_category, True)
        self.assertEqual(self.forum.is_category, False)

    def test_children(self):
        self.assertEqual(self.forum.children, [])
        self.assertEqual(self.parent.children, [self.forum])
        self.assertEqual(self.category.children, [self.parent])

    def test_get_children_recursive(self):
        rec = list(Forum.get_children_recursive((self.forum, self.category, self.parent)))
        rec2 = list(Forum.get_children_recursive((self.forum,)))
        rec3 = list(Forum.get_children_recursive((self.parent,)))
        rec4 = list(Forum.get_children_recursive((self.parent,), self.category))

        self.assertEqual(rec, [(0, self.category), (1, self.parent), (2, self.forum)])
        self.assertEqual(rec2, [])
        self.assertEqual(rec3, [])
        self.assertEqual(rec4, [(0, self.parent)])

    def test_descendants(self):
        self.assertEqual(self.forum.descendants, [])
        self.assertEqual(self.parent.descendants, [self.forum])
        self.assertEqual(self.category.descendants, [self.parent, self.forum])

    def test_get_slugs(self):
        slug_map = {self.category.id: 'category',
                    self.parent.id: 'parent',
                    self.forum.id: 'forum'}
        cache.delete('forum/slugs')

        self.assertEqual(cache.get('forum/slugs'), None)
        self.assertEqual(Forum.objects.get_slugs(), slug_map)
        self.assertEqual(cache.get('forum/slugs'), slug_map)

    def test_get_ids(self):
        self.assertEqual(set(Forum.objects.get_ids()),
                         {self.category.id, self.parent.id, self.forum.id})

    def test_unified_get(self):
        cache.delete('forum/forums/%s' % self.forum.slug)

        self.assertEqual(self.forum, Forum.objects.get(self.forum.id))
        self.assertEqual(cache.get('forum/forums/%s' % self.forum.slug), self.forum)
        self.assertEqual(self.forum, Forum.objects.get(self.forum.slug))
        self.assertEqual(self.forum, Forum.objects.get(id=self.forum.id))
        self.assertEqual(self.forum, Forum.objects.get(slug=self.forum.slug))

    def test_get_all_forums_cached(self):
        cache_key_map = {'forum/forums/category': self.category,
                         'forum/forums/parent': self.parent,
                         'forum/forums/forum': self.forum}
        cache.delete_many(list(cache_key_map.keys()))
        cache.delete('forum/slugs')

        cached_forums = Forum.objects.get_all_forums_cached()

        self.assertEqual(cached_forums, cache_key_map)
        self.assertEqual(cache.get('forum/forums/category'), self.category)

    def test_update_get_all_forums_cached_on_forum_creation(self):
        cache_key_map = {'forum/forums/category': self.category,
                         'forum/forums/parent': self.parent,
                         'forum/forums/forum': self.forum}
        cache.delete_many(list(cache_key_map.keys()))
        cache.delete('forum/slugs')
        Forum.objects.get_all_forums_cached()

        new_forum = Forum(name='yeha')
        new_forum.save()
        cache_key_map.update({'forum/forums/yeha': new_forum})

        self.assertEqual(cache.get('forum/forums/yeha'), None)
        self.assertEqual(Forum.objects.get_all_forums_cached(), cache_key_map)
        self.assertEqual(cache.get('forum/forums/yeha'), new_forum)

    def test_get_absolute_url(self):
        forum_url = self.forum.get_absolute_url('show', foo='val1', bar='val2')

        expected_url = ''.join([
            'http://forum.', settings.BASE_DOMAIN_NAME,
            '/forum/', self.forum.slug, '/',
            '?foo=val1&bar=val2'
        ])
        self.assertURLEqual(forum_url, expected_url)


class TestPostModel(ForumTestCase):

    @override_settings(BASE_DOMAIN_NAME='inyoka.local')
    def test_url_for_post(self):
        post = Post(text='test1', author=self.user, topic=self.topic)
        post.save()

        self.assertEqual(Post.url_for_post(post.pk),
                         'http://forum.inyoka.local/topic/topic/#post-%s' % post.pk)

    @override_settings(BASE_DOMAIN_NAME='inyoka.local')
    def test_url_for_post_multiple_pages(self):
        posts = self.addPosts(45)
        last_post_id = list(posts)[-1].pk

        self.assertEqual(Post.url_for_post(last_post_id),
                         'http://forum.inyoka.local/topic/topic/4/#post-%s' % last_post_id)

    def test_url_for_post_not_existing_post(self):
        self.assertRaises(Post.DoesNotExist, Post.url_for_post, 250000913)

    def test_rendered_get_text(self):
        post = Post(text="'''test'''")

        self.assertEqual(post.get_text(), "<p><strong>test</strong></p>")

    def test_plaintext_get_text(self):
        post = Post(text="'''test'''", is_plaintext=True)

        self.assertEqual(post.get_text(), "&#39;&#39;&#39;test&#39;&#39;&#39;")


class TestPostRevisionModel(TestCase):

    def test_text_rendered(self):
        r = PostRevision(text="'''test'''")

        self.assertEqual(r.text_rendered, "<p><strong>test</strong></p>")


class TestPostSplit(ForumTestCaseWithSecondItems):

    def test_post_counter(self):
        self.assertEqual(self.user.post_count.value(), 5)

    def test_topic_count(self):
        self.assertEqual(self.topic.post_count.value(), 5)
        self.assertEqual(self.other_topic.post_count.value(), 5)

    def test_topic_first_post(self):
        self.assertEqual(self.topic.first_post, self.topic_posts[0])
        self.assertEqual(self.other_topic.first_post, self.other_topic_posts[0])

    def test_topic_last_post(self):
        self.assertEqual(self.topic.last_post, self.topic_posts[-1])
        self.assertEqual(self.other_topic.last_post, self.other_topic_posts[-1])

    def test_split_renumber_old_positions(self):
        posts_to_split = Post.objects.filter(topic=self.topic, position__in=[1, 2, 4])

        Post.split(posts_to_split, self.topic, self.other_topic)

        positions_after_split = Post.objects.filter(topic=self.topic)\
            .order_by('position')\
            .values_list('position', flat=True)
        self.assertEqual(list(positions_after_split), [1, 2])

    def test_split_post_remove_topic(self):
        post_ids = [post.id for post in (self.other_topic_posts + self.topic_posts)]

        Post.split(self.topic_posts, self.topic, self.other_topic)

        cache.delete('forum/forums/%s' % self.forum.slug)
        cache.delete('forum/forums/%s' % self.other_forum.slug)
        self.other_topic.refresh_from_db()
        self.assertFalse(Topic.objects.filter(id=self.topic.id).exists())
        self.assertEqual(self.other_topic.post_count.value(), 10)
        self.assertEqual(self.other_topic.first_post.id, self.other_topic_posts[0].id)
        self.assertEqual(self.other_topic.last_post.id, self.topic_posts[4].id)
        self.assertEqual([post.id for post in self.other_topic.posts.order_by('position')], post_ids)

    def test_split_topic_post_count(self):
        """
        Tests that the post_count of the new topic is correct after the split.
        """
        Post.split(self.topic.posts.all(), self.topic, self.other_topic)

        self.assertEqual(
            self.other_topic.post_count.value(),
            self.other_topic.posts.count())


class TestPostMove(ForumTestCaseWithSecondItems):

    def test_post_counter(self):
        self.assertEqual(self.user.post_count(), 5)

    def test_topic_count(self):
        self.assertEqual(self.topic.post_count.value(), 5)
        self.assertEqual(self.other_topic.post_count.value(), 5)

    def test_topic_move(self):
        self.topic.move(self.other_forum)

        self.topic.refresh_from_db()
        self.forum.refresh_from_db()
        self.parent.refresh_from_db()
        self.category.refresh_from_db()
        self.assertEqual(self.user.post_count(), 0)
        self.assertEqual(self.topic.post_count.value(), 5)
        self.assertEqual(self.topic.last_post, self.topic_posts[-1])
        self.assertEqual(self.topic.forum.last_post, self.other_topic_posts[-1])
        self.assertEqual(self.forum.last_post, None)
        self.assertEqual(self.parent.last_post, None)
        self.assertEqual(self.category.last_post, None)

    def test_topic_move__topic_in_forum_left(self):
        """This adds another topic to self.forum. Thus, a topic is still left in self.forum."""
        second_topic_in_forum = Topic.objects.create(title='topic1_2', author=self.user, forum=self.forum)
        second_topic_posts = list(self.addPosts(2, second_topic_in_forum))

        self.topic.move(self.other_forum)

        self.topic.refresh_from_db()
        self.forum.refresh_from_db()
        self.parent.refresh_from_db()
        self.category.refresh_from_db()
        self.assertEqual(self.user.post_count(), len(second_topic_posts))
        self.assertEqual(self.topic.post_count.value(), 5)
        self.assertEqual(self.topic.last_post, self.topic_posts[-1])
        self.assertEqual(self.topic.forum.last_post, self.other_topic_posts[-1])
        self.assertEqual(self.forum.last_post, second_topic_posts[-1])
        self.assertEqual(self.parent.last_post, second_topic_posts[-1])
        self.assertEqual(self.category.last_post, second_topic_posts[-1])


class PostDeletionTest(ForumTestCase):

    def setUp(self):
        super(PostDeletionTest, self).setUp()

        self.first_post = self.topic_posts[0]
        self.second_last_post = self.topic_posts[-2]
        self.last_post = self.topic_posts[-1]

    def test_cache_is_cleared_after_deletion(self):
        forum_cache_keys = list(Forum.objects.get_all_forums_cached().keys())
        cached_forums = cache.get_many(forum_cache_keys)
        self.assertEqual(cached_forums['forum/forums/category'].last_post_id, self.last_post.pk)
        self.assertEqual(cached_forums['forum/forums/parent'].last_post_id, self.last_post.pk)
        self.assertEqual(cached_forums['forum/forums/forum'].last_post_id, self.last_post.pk)

        Post.objects.get(pk=self.last_post.pk).delete()

        cached_forums = cache.get_many(forum_cache_keys)
        self.assertEqual(cached_forums, {})

    def test_last_post_is_updated(self):
        Post.objects.get(pk=self.last_post.pk).delete()

        self.category.refresh_from_db()
        self.parent.refresh_from_db()
        self.forum.refresh_from_db()
        self.assertEqual(self.category.last_post_id, self.second_last_post.pk)
        self.assertEqual(self.parent.last_post_id, self.second_last_post.pk)
        self.assertEqual(self.forum.last_post_id, self.second_last_post.pk)

    def test_post_delete_at_end(self):
        # Warm up cache
        forum_cache_keys = list(Forum.objects.get_all_forums_cached().keys())
        cached_forums = cache.get_many(forum_cache_keys)
        self.assertEqual(cached_forums['forum/forums/category'].last_post_id, self.last_post.pk)
        self.assertEqual(cached_forums['forum/forums/parent'].last_post_id, self.last_post.pk)
        self.assertEqual(cached_forums['forum/forums/forum'].last_post_id, self.last_post.pk)

        # trigger post deletion
        Post.objects.get(pk=self.last_post.pk).delete()
        # ensure cache is properly pruned
        cached_forums = cache.get_many(forum_cache_keys)
        self.assertEqual(cached_forums, {})

        # last post got changed
        topic = Topic.objects.get(pk=self.topic.pk)
        self.assertEqual(topic.last_post_id, self.second_last_post.pk)

        # forum.last_post is correct
        forums = [f for f in topic.forum.parents + [topic.forum] if f.last_post]
        last_post_ids = [f.last_post_id for f in forums]
        self.assertEqual(last_post_ids, [self.second_last_post.pk, self.second_last_post.pk, self.second_last_post.pk])

        # refresh cache, check for proper last_post_id
        Forum.objects.get_all_forums_cached()
        cached_forums = cache.get_many(forum_cache_keys)
        self.assertEqual(cached_forums['forum/forums/category'].last_post_id, self.second_last_post.pk)
        self.assertEqual(cached_forums['forum/forums/parent'].last_post_id, self.second_last_post.pk)
        self.assertEqual(cached_forums['forum/forums/forum'].last_post_id, self.second_last_post.pk)

    def test_post_delete_at_center(self):
        # last post wasn't changed
        topic = Topic.objects.get(pk=self.topic.pk)

        # trigger post deletion
        Post.objects.get(pk=self.second_last_post.pk).delete()
        self.assertEqual(topic.last_post_id, self.last_post.pk)
        # postions are still correct
        p1 = Post.objects.get(pk=self.first_post.pk)
        self.assertEqual(p1.position, 1)
        p1 = Post.objects.get(pk=self.last_post.pk)
        self.assertEqual(p1.position, 4)
        # forum.last_post is correct
        forums = [f for f in topic.forum.parents + [topic.forum] if f.last_post]
        last_post_ids = [f.last_post_id for f in forums]
        self.assertEqual(last_post_ids, [self.last_post.pk, self.last_post.pk, self.last_post.pk])


class TestTopic(ForumTestCase):

    @patch.object(Topic, 'delete')
    def test_topic_delete(self, mock):
        """Tests if the .delete() of posts is called. """
        self.topic = Topic.objects.create(forum=self.forum, title='test',
                                          author=self.user)
        self.attachment = Attachment.create('test.txt', ContentFile('test'), 'text/plain', [])
        self.p1 = Post.objects.create(text='', author=self.user, topic=self.topic, position=0)
        self.p1.attachment = self.attachment
        self.p1.has_attachments = True

        self.topic.delete()
        mock.assert_called_once_with()
