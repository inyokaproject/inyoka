"""
    tests.apps.portal.test_tasks
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test celery tasks of portal

    :copyright: (c) 2007-2025 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime, timezone

from django.utils import timezone as dj_timezone

from inyoka.planet.models import Blog
from inyoka.planet.models import Entry as BlogEntry
from inyoka.portal.tasks import _clean_expired_users, _clean_inactive_users
from inyoka.portal.user import User
from inyoka.utils.test import TestCase


class TestCleanInactiveUsers(TestCase):

    def setUp(self):
        super().setUp()
        self.user = User.objects.register_user(
            'testing',
            'example@example.com',
            'pwd',
            False
        )

    def test_clean_inactive_users__user_with_blog_preserved(self):
        self.user.last_login = datetime(2010, 1, 1, tzinfo=timezone.utc)
        self.user.save()

        blog = Blog.objects.create(name="Testblog", blog_url="http://example.com/",
                    feed_url="http://example.com/feed", user=self.user,
                    active=True)

        BlogEntry.objects.create(blog=blog, url="http://example.com/article1",
                             guid="http://example.com/article1",
                             text="This is a test", title="title",
                             pub_date=dj_timezone.now(),
                             updated=dj_timezone.now())

        self.assertEqual(Blog.objects.count(), 1)
        self.assertEqual(BlogEntry.objects.count(), 1)

        _clean_inactive_users()

        self.assertEqual(Blog.objects.count(), 1)
        self.assertEqual(BlogEntry.objects.count(), 1)

    def test_clean_inactive_users__user_deleted(self):
        self.user.last_login = datetime(2010, 1, 1, tzinfo=timezone.utc)
        self.user.save()

        _clean_inactive_users()

        self.assertFalse(User.objects.filter(username=self.user.username).exists())


class TestCleanExpiredUsers(TestCase):

    def setUp(self):
        super().setUp()
        self.user = User.objects.create(
            username='testing',
            email='example@example.com',
            date_joined=datetime(2010, 1, 1, tzinfo=timezone.utc),
        )

    def test_clean_expired_users__user_deleted(self):
        _clean_expired_users()

        self.assertFalse(User.objects.filter(username=self.user.username).exists())

    def test_clean_expired_users__ignores_activated_user(self):
        self.user.status = User.STATUS_ACTIVE
        self.user.save()

        _clean_expired_users()

        self.assertTrue(User.objects.filter(username=self.user.username).exists())
