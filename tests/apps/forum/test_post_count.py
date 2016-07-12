# -*- coding: utf-8 -*-

from mock import patch

from inyoka.forum.models import Forum, Post, Topic
from inyoka.portal.user import User
from inyoka.utils.test import TestCase


class TestForumPostCount(TestCase):
    def test_with_empty_cache(self):
        """
        Test to call forum.post_count.value() when the cache was not created.
        """
        user = User.objects.create(username='test_user',email='test_user')
        forum = Forum.objects.create(name='This is a test')
        topic = Topic.objects.create(title='topic', author=user, forum=forum)
        Post.objects.create(text='content', author=user, topic=topic)

        self.assertEqual(forum.post_count.value(), 1)

    def test_with_existing_cache(self):
        """
        Test when the cache was created.
        """
        user = User.objects.create(username='test_user',email='test_user')
        forum = Forum.objects.create(name='This is a test')
        topic = Topic.objects.create(title='topic', author=user, forum=forum)
        forum.post_count.db_count(write_cache=True)  # Create the cache
        Post.objects.create(text='content', author=user, topic=topic)

        self.assertEqual(forum.post_count.value(), 1)

    def test_with_empty_cache_call_db_count(self):
        """
        Test to call forum.post_count.value() when the cache was not created.

        In this case forum.post_count.db_count should be called to calculate
        the value.
        """
        user = User.objects.create(username='test_user',email='test_user')
        forum = Forum.objects.create(name='This is a test')
        topic = Topic.objects.create(title='topic', author=user, forum=forum)
        Post.objects.create(text='content', author=user, topic=topic)

        with patch.object(forum.post_count, 'db_count') as mock_db_count:
            mock_db_count.return_value = 1
            forum.post_count.value()

        mock_db_count.assert_called_once_with()

    def test_with_existing_cache_call_db_count(self):
        """
        Test when the cache was created. In this case db_count should not be
        called.
        """
        user = User.objects.create(username='test_user',email='test_user')
        forum = Forum.objects.create(name='This is a test')
        topic = Topic.objects.create(title='topic', author=user, forum=forum)
        forum.post_count.db_count(write_cache=True)  # Create the cache
        Post.objects.create(text='content', author=user, topic=topic)

        with patch.object(forum.post_count, 'db_count') as mock_db_count:
            mock_db_count.return_value = 1
            forum.post_count.value()

        mock_db_count.assert_not_called()

    def test_on_sub_forum_empty_cache(self):
        user = User.objects.create(username='test_user',email='test_user')
        forum = Forum.objects.create(name='This is a test')
        sub_forum = Forum.objects.create(name='This is a test', parent=forum)
        topic = Topic.objects.create(title='topic', author=user, forum=sub_forum)
        Post.objects.create(text='content', author=user, topic=topic)

        self.assertEqual(forum.post_count.value(), 1)

    def test_on_sub_forum_existing_cache(self):
        user = User.objects.create(username='test_user',email='test_user')
        forum = Forum.objects.create(name='This is a test')
        sub_forum = Forum.objects.create(name='This is a test', parent=forum)
        topic = Topic.objects.create(title='topic', author=user, forum=sub_forum)
        forum.post_count.db_count(write_cache=True)
        Post.objects.create(text='content', author=user, topic=topic)

        self.assertEqual(forum.post_count.value(), 1)

    def test_on_sub_sub_forum_empty_cache(self):
        user = User.objects.create(username='test_user',email='test_user')
        forum = Forum.objects.create(name='This is a test')
        sub_forum = Forum.objects.create(name='This is a test', parent=forum)
        sub_sub_forum = Forum.objects.create(name='This is a test', parent=sub_forum)
        topic = Topic.objects.create(title='topic', author=user, forum=sub_sub_forum)
        Post.objects.create(text='content', author=user, topic=topic)

        self.assertEqual(forum.post_count.value(), 1)


class TestForumTopicCount(TestCase):
    def test_with_empty_cache(self):
        """
        Test to call forum.topic_count.value() when the cache was not created.
        """
        user = User.objects.create(username='test_user',email='test_user')
        forum = Forum.objects.create(name='This is a test')
        Topic.objects.create(title='topic', author=user, forum=forum)

        self.assertEqual(forum.topic_count.value(), 1)

    def test_with_existing_cache(self):
        """
        Test when the cache was created.
        """
        user = User.objects.create(username='test_user',email='test_user')
        forum = Forum.objects.create(name='This is a test')
        forum.topic_count.db_count(write_cache=True)  # Create the cache
        Topic.objects.create(title='topic', author=user, forum=forum)

        self.assertEqual(forum.topic_count.value(), 1)

    def test_with_empty_cache_call_db_count(self):
        """
        Test to call forum.topic_count.value() when the cache was not created.

        In this case forum.topic_count.db_count should be called to calculate
        the value.
        """
        user = User.objects.create(username='test_user',email='test_user')
        forum = Forum.objects.create(name='This is a test')
        Topic.objects.create(title='topic', author=user, forum=forum)

        with patch.object(forum.topic_count, 'db_count') as mock_db_count:
            mock_db_count.return_value = 1
            forum.topic_count.value()

        mock_db_count.assert_called_once_with()

    def test_with_existing_cache_call_db_count(self):
        """
        Test when the cache was created. In this case db_count should not be
        called.
        """
        user = User.objects.create(username='test_user',email='test_user')
        forum = Forum.objects.create(name='This is a test')
        forum.topic_count.db_count(write_cache=True)  # Create the cache
        Topic.objects.create(title='topic', author=user, forum=forum)

        with patch.object(forum.topic_count, 'db_count') as mock_db_count:
            mock_db_count.return_value = 1
            forum.topic_count.value()

        mock_db_count.assert_not_called()

    def test_on_sub_forum_empty_cache(self):
        user = User.objects.create(username='test_user',email='test_user')
        forum = Forum.objects.create(name='This is a test')
        sub_forum = Forum.objects.create(name='This is a test', parent=forum)
        Topic.objects.create(title='topic', author=user, forum=sub_forum)

        self.assertEqual(forum.topic_count.value(), 0)

    def test_on_sub_forum_existing_cache(self):
        user = User.objects.create(username='test_user',email='test_user')
        forum = Forum.objects.create(name='This is a test')
        sub_forum = Forum.objects.create(name='This is a test', parent=forum)
        forum.post_count.db_count(write_cache=True)
        Topic.objects.create(title='topic', author=user, forum=sub_forum)

        self.assertEqual(forum.topic_count.value(), 0)

    def test_on_sub_sub_forum_empty_cache(self):
        user = User.objects.create(username='test_user',email='test_user')
        forum = Forum.objects.create(name='This is a test')
        sub_forum = Forum.objects.create(name='This is a test', parent=forum)
        sub_sub_forum = Forum.objects.create(name='This is a test', parent=sub_forum)
        Topic.objects.create(title='topic', author=user, forum=sub_sub_forum)

        self.assertEqual(forum.topic_count.value(), 0)
