# -*- coding: utf-8 -*-

from mock import patch

from inyoka.forum.models import Forum, Post, Topic
from inyoka.portal.user import User
from inyoka.utils.test import TestCase


class TestForumPostCount(TestCase):

    def setUp(self):
        super(TestCase, self).setUp()
        self.user = User.objects.create(username='test_user', email='test_user')
        self.forum = Forum.objects.create(name='This is a test')
        self.topic = Topic.objects.create(title='topic', author=self.user, forum=self.forum)

    def test_with_empty_cache(self):
        """
        Test to call forum.post_count.value() when the cache was not created.
        """
        Post.objects.create(text='content', author=self.user, topic=self.topic)

        self.assertEqual(self.forum.post_count.value(), 1)

    def test_with_existing_cache(self):
        """
        Test when the cache was created.
        """
        self.forum.post_count.db_count(write_cache=True)  # Create the cache
        Post.objects.create(text='content', author=self.user, topic=self.topic)

        self.assertEqual(self.forum.post_count.value(), 1)

    def test_with_empty_cache_call_db_count(self):
        """
        Test to call forum.post_count.value() when the cache was not created.

        In this case forum.post_count.db_count should be called to calculate
        the value.
        """
        Post.objects.create(text='content', author=self.user, topic=self.topic)

        with patch.object(self.forum.post_count, 'db_count') as mock_db_count:
            mock_db_count.return_value = 1
            self.forum.post_count.value()

        mock_db_count.assert_called_once_with()

    def test_with_existing_cache_call_db_count(self):
        """
        Test when the cache was created. In this case db_count should not be
        called.
        """
        self.forum.post_count.db_count(write_cache=True)  # Create the cache
        Post.objects.create(text='content', author=self.user, topic=self.topic)

        with patch.object(self.forum.post_count, 'db_count') as mock_db_count:
            mock_db_count.return_value = 1
            self.forum.post_count.value()

        mock_db_count.assert_not_called()

    def test_on_sub_forum_empty_cache(self):
        sub_forum = Forum.objects.create(name='This is a test', parent=self.forum)
        topic = Topic.objects.create(title='topic', author=self.user, forum=sub_forum)
        Post.objects.create(text='content', author=self.user, topic=topic)

        self.assertEqual(self.forum.post_count.value(), 1)

    def test_on_sub_forum_existing_cache(self):
        sub_forum = Forum.objects.create(name='This is a test', parent=self.forum)
        topic = Topic.objects.create(title='topic', author=self.user, forum=sub_forum)
        self.forum.post_count.db_count(write_cache=True)
        Post.objects.create(text='content', author=self.user, topic=topic)

        self.assertEqual(self.forum.post_count.value(), 1)

    def test_on_sub_sub_forum_empty_cache(self):
        sub_forum = Forum.objects.create(name='This is a test', parent=self.forum)
        sub_sub_forum = Forum.objects.create(name='This is a test', parent=sub_forum)
        topic = Topic.objects.create(title='topic', author=self.user, forum=sub_sub_forum)
        Post.objects.create(text='content', author=self.user, topic=topic)

        self.assertEqual(self.forum.post_count.value(), 1)


class TestForumTopicCount(TestCase):

    def setUp(self):
        super(TestCase, self).setUp()
        self.user = User.objects.create(username='test_user', email='test_user')
        self.forum = Forum.objects.create(name='This is a test')

    def test_with_empty_cache(self):
        """
        Test to call forum.topic_count.value() when the cache was not created.
        """
        Topic.objects.create(title='topic', author=self.user, forum=self.forum)

        self.assertEqual(self.forum.topic_count.value(), 1)

    def test_with_existing_cache(self):
        """
        Test when the cache was created.
        """
        self.forum.topic_count.db_count(write_cache=True)  # Create the cache
        Topic.objects.create(title='topic', author=self.user, forum=self.forum)

        self.assertEqual(self.forum.topic_count.value(), 1)

    def test_with_empty_cache_call_db_count(self):
        """
        Test to call forum.topic_count.value() when the cache was not created.

        In this case forum.topic_count.db_count should be called to calculate
        the value.
        """
        Topic.objects.create(title='topic', author=self.user, forum=self.forum)

        with patch.object(self.forum.topic_count, 'db_count') as mock_db_count:
            mock_db_count.return_value = 1
            self.forum.topic_count.value()

        mock_db_count.assert_called_once_with()

    def test_with_existing_cache_call_db_count(self):
        """
        Test when the cache was created. In this case db_count should not be
        called.
        """
        self.forum.topic_count.db_count(write_cache=True)  # Create the cache
        Topic.objects.create(title='topic', author=self.user, forum=self.forum)

        with patch.object(self.forum.topic_count, 'db_count') as mock_db_count:
            mock_db_count.return_value = 1
            self.forum.topic_count.value()

        mock_db_count.assert_not_called()

    def test_on_sub_forum_empty_cache(self):
        sub_forum = Forum.objects.create(name='This is a test', parent=self.forum)
        Topic.objects.create(title='topic', author=self.user, forum=sub_forum)

        self.assertEqual(self.forum.topic_count.value(), 0)

    def test_on_sub_forum_existing_cache(self):
        sub_forum = Forum.objects.create(name='This is a test', parent=self.forum)
        self.forum.post_count.db_count(write_cache=True)
        Topic.objects.create(title='topic', author=self.user, forum=sub_forum)

        self.assertEqual(self.forum.topic_count.value(), 0)

    def test_on_sub_sub_forum_empty_cache(self):
        sub_forum = Forum.objects.create(name='This is a test', parent=self.forum)
        sub_sub_forum = Forum.objects.create(name='This is a test', parent=sub_forum)
        Topic.objects.create(title='topic', author=self.user, forum=sub_sub_forum)

        self.assertEqual(self.forum.topic_count.value(), 0)
