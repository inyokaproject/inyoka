# -*- coding: utf-8 -*-
"""
    tests.apps.portal.test_user
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test some user model functions

    :copyright: (c) 2007-2016 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import unittest
from datetime import datetime

from django.core.cache import cache

from inyoka.forum.models import Forum, Post, Topic
from inyoka.ikhaya.models import Article, Category, Comment, Event, Suggestion
from inyoka.pastebin.models import Entry
from inyoka.portal.models import Subscription
from inyoka.portal.user import Group, User, deactivate_user
from inyoka.utils.test import TestCase
from inyoka.wiki.models import Page


class TestUserModel(TestCase):
    def setUp(self):
        self.user = User.objects.register_user('testing', 'example@example.com',
                                               'pwd', False)

    def test_deactivation(self):
        """Test if the user status is correctly changed after deactivating a
        user.
        """
        deactivate_user(self.user)
        self.user = User.objects.get(pk=self.user.id)
        self.assertEqual(self.user.status, 3)

    def test_get_user_by_username(self):
        user = User.objects.get_by_username_or_email('testing')
        self.assertEqual(user, self.user)

    def test_get_user_by_email(self):
        user = User.objects.get_by_username_or_email('example@example.com')
        self.assertEqual(user, self.user)

    def test_get_user_fails(self):
        User.objects.register_user('foo@bar.d', 'foo@bar.de', 'pwd', False)
        with self.assertRaises(User.DoesNotExist):
            User.objects.get_by_username_or_email('foo@bar')

    def test_rename_user(self):
        created_user = User.objects.register_user('testuser', 'test@user.de', 'pwd', False)
        self.assertTrue(created_user.rename('testuser2', False))
        self.assertEqual(unicode(created_user), 'testuser2')

    def test_rename_user_collision(self):
        User.objects.register_user('testuser3', 'test3@user.de', 'pwd', False)
        created_user = User.objects.register_user('testuser4', 'test4@user.de', 'pwd', False)
        self.assertFalse(created_user.rename('testuser3', False))

    def test_rename_user_invalid(self):
        created_user = User.objects.register_user('testuser5', 'test5@user.de', 'pwd', False)
        with self.assertRaisesRegexp(ValueError, 'invalid username'):
            created_user.rename('**testuser**', False)


class TestUserHasContent(TestCase):
    def setUp(self):
        self.user = User.objects.register_user(
            'testing',
            'example@example.com',
            'pwd', False)

    def test_no_content(self):
        self.assertFalse(self.user.has_content())

    def test_post_count(self):
        cache.set(self.user.post_count.cache_key, 1)
        self.assertTrue(self.user.has_content())

    def test_has_forum_posts(self):
        """
        Test a user with one forum post in a forum that does not change the
        users posts, so self.user.post_count is 0 in a topic from another user.
        """
        other_user = User.objects.register_user(
            'other_user',
            'example2@example.com',
            'pwd', False)
        forum = Forum.objects.create(user_count_posts=False)
        topic = Topic.objects.create(forum=forum, author=other_user)
        Post.objects.create(author=self.user, topic=topic)

        self.assertTrue(self.user.has_content())

    def test_has_forum_topics(self):
        """
        Test a user as author from a topic with no posts.
        """
        # This test can be deleted when the field Topic.author is removed
        forum = Forum.objects.create(user_count_posts=False)
        Topic.objects.create(forum=forum, author=self.user)

        self.assertTrue(self.user.has_content())

    @unittest.skip("Django Bug")
    def test_ikhaya_article(self):
        """
        Tests a user that is an author of an Ikhaya article
        """
        # There seems to be an Bug in django, that user.article_set does not
        # work.
        now = datetime.now()
        category = Category.objects.create(name='test_category')

        Article.objects.create(
            pub_date=now.date(),
            pub_time=now.time(),
            author=self.user,
            category=category)

        self.assertTrue(self.user.has_content())

    def test_ikhaya_comment(self):
        now = datetime.now()
        category = Category.objects.create(name='test_category')
        other_user = User.objects.register_user(
            'other_user',
            'example2@example.com',
            'pwd', False)
        article = Article.objects.create(
            pub_date=now.date(),
            pub_time=now.time(),
            author=other_user,
            category=category)
        Comment.objects.create(
            author=self.user,
            article=article,
            pub_date=now)

        self.assertTrue(self.user.has_content())

    def test_ikhaya_suggestion(self):
        other_user = User.objects.register_user(
            'other_user',
            'example2@example.com',
            'pwd', False)
        Suggestion.objects.create(author=self.user, owner=other_user)

        self.assertTrue(self.user.has_content())
        self.assertTrue(other_user.has_content())

    def test_wiki_page(self):
        Page.objects.create('foo', 'bar', self.user)

        self.assertTrue(self.user.has_content())

    def test_pastebin(self):
        Entry.objects.create(author=self.user)

        self.assertTrue(self.user.has_content())

    def test_event(self):
        now = datetime.now()
        Event.objects.create(author=self.user, date=now.date())

        self.assertTrue(self.user.has_content())

    def test_subscription(self):
        other_user = User.objects.register_user(
            'other_user',
            'example2@example.com',
            'pwd', False)
        forum = Forum.objects.create(user_count_posts=False)
        topic = Topic.objects.create(forum=forum, author=other_user)
        Subscription.objects.create(user=self.user, content_object=topic)

        self.assertTrue(self.user.has_content())


class TestGroupModel(TestCase):
    def setUp(self):
        self.group = Group.objects.create(name='testing', is_public=True)

    def test_icon(self):
        # TODO? What should be tested here?
        self.assertEqual(self.group.icon_url, None)
