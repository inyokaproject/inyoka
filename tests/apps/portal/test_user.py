"""
    tests.apps.portal.test_user
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test some user model functions

    :copyright: (c) 2007-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import unittest
from datetime import UTC, datetime, timedelta

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.core.exceptions import ValidationError

from inyoka.forum.models import Forum, Post, Topic
from inyoka.ikhaya.models import Article, Category, Comment, Event, Suggestion
from inyoka.pastebin.models import Entry
from inyoka.portal.models import PrivateMessage, Subscription
from inyoka.portal.user import User, deactivate_user, reactivate_user
from inyoka.utils.test import TestCase
from inyoka.wiki.models import Page


class TestUserModel(TestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.register_user('testing', 'example@example.com',
                                               'pwd', False)

    def test_deactivation(self):
        """Test if the user status is correctly changed after deactivating a
        user.
        """
        deactivate_user(self.user)
        self.user = User.objects.get(pk=self.user.id)
        self.assertTrue(self.user.is_deleted)

    def test_email_exists(self):
        with self.assertRaisesMessage(ValidationError,
                                      'This e-mail address is used by another user.'):
            reactivate_user(self.user.id, self.user.email, self.user.status)

    def test_user_is_already_reactivated(self):
        with self.assertRaisesMessage(ValidationError,
                                      'The account “testing” was already reactivated.'):
            reactivate_user(self.user.id, 'test@example.com', self.user.status)

    def test_user_reactivate_after_ban_exceeded(self):
        """Test that a user, whose ban time exceeded, can reactivate the account.
        """
        banned_user = User.objects.register_user('banned',
                                                 'ban@example.com',
                                                 'pwd',
                                                 False)
        banned_user.banned_until = datetime.now(UTC) - timedelta(days=5)
        deactivate_user(banned_user)
        banned_user.refresh_from_db()

        reactivate_user(banned_user.id, 'ban@example.com', banned_user.status)
        banned_user.refresh_from_db()

        self.assertEqual(banned_user.status, User.STATUS_ACTIVE)
        self.assertIsNone(banned_user.banned_until)

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
        self.assertEqual(str(created_user), 'testuser2')

    def test_rename_user_collision(self):
        User.objects.register_user('testuser3', 'test3@user.de', 'pwd', False)
        created_user = User.objects.register_user('testuser4', 'test4@user.de', 'pwd', False)
        self.assertFalse(created_user.rename('testuser3', False))

    def test_rename_user_invalid(self):
        created_user = User.objects.register_user('testuser5', 'test5@user.de', 'pwd', False)
        with self.assertRaisesRegex(ValueError, 'invalid username'):
            created_user.rename('**testuser**', False)

    def test_new_users_in_registered_group(self):
        registered_group = Group.objects.get(name=settings.INYOKA_REGISTERED_GROUP_NAME)
        self.assertTrue(registered_group in self.user.groups.all())

    def test_anonymous_is_not_team_member(self):
        anonymous = User.objects.get_anonymous_user()
        self.assertFalse(anonymous.is_team_member)

    def test_is_not_team_member(self):
        self.assertFalse(self.user.is_team_member)

    def test_is_team_member(self):
        team_group = Group.objects.get(name=settings.INYOKA_TEAM_GROUP_NAME)
        self.user.groups.add(team_group)
        self.assertTrue(self.user.is_team_member)


class TestUserHasContent(TestCase):
    def setUp(self):
        super().setUp()
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

    def test_privatemessage(self):
        """
        Test privatemessage as sender and receiver.
        """
        now = datetime.now()
        other_user = User.objects.register_user(
            'other_user',
            'example2@example.com',
            'pwd', False)
        pm = PrivateMessage(author=self.user, pub_date=now)
        pm.send([other_user])

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
