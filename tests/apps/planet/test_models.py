"""
tests.apps.planet.test_models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test planet models.

:copyright: (c) 2012-2026 by the Inyoka Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from django.conf import settings
from django.db.models import ProtectedError
from django.test import TestCase
from django.utils import timezone as dj_timezone

from inyoka.planet.models import Blog
from inyoka.planet.models import Entry as BlogEntry
from inyoka.portal.user import User


class TestBlogModel(TestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.register_user(
            'testing', 'example@example.com', 'pwd', False
        )

        self.blog = Blog.objects.create(
            name='Testblog',
            blog_url='http://example.com/',
            feed_url='http://example.com/feed',
            user=self.user,
            active=True,
        )

    def test_delete_user__preserves_blog_via_protected_error(self):
        BlogEntry.objects.create(
            blog=self.blog,
            url='http://example.com/article1',
            guid='http://example.com/article1',
            text='This is a test',
            title='title',
            pub_date=dj_timezone.now(),
            updated=dj_timezone.now(),
        )

        self.assertEqual(Blog.objects.count(), 1)
        self.assertEqual(BlogEntry.objects.count(), 1)

        with self.assertRaisesMessage(
            ProtectedError,
            "Cannot delete some instances of model 'User' because they are referenced through protected foreign keys: 'Blog.user'.",
        ):
            self.user.delete()

        self.assertEqual(Blog.objects.count(), 1)
        self.assertEqual(BlogEntry.objects.count(), 1)

    def test_icon_url(self):
        self.assertIsNone(self.blog.icon_url)

        self.blog.icon = 'foo.png'
        self.blog.save()
        self.blog.refresh_from_db()
        self.assertEqual(
            self.blog.icon_url, f'//media.{settings.BASE_DOMAIN_NAME}/foo.png'
        )

    def test_icon_deleted(self):
        self.blog.icon = 'foo.png'
        self.blog.save()

        self.blog.delete()
        self.assertEqual(Blog.objects.count(), 0)

    def test_absolute_url_show(self):
        self.assertEqual(self.blog.get_absolute_url(), 'http://example.com/')

    def test_absolute_url_edit(self):
        self.assertEqual(
            self.blog.get_absolute_url('edit'),
            f'http://planet.{settings.BASE_DOMAIN_NAME}/blog/1/edit/',
        )


class TestEntryModel(TestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.register_user(
            'testing', 'example@example.com', 'pwd', False
        )

        self.blog = Blog.objects.create(
            name='Testblog',
            blog_url='https://example.test/',
            feed_url='https://example.test/feed.xml',
            user=self.user,
            active=True,
        )

        self.entry = BlogEntry.objects.create(
            blog=self.blog,
            url='https://example.test/a1',
            guid='https://example.test/a1',
            text='There <em>is</em> some test',
            title='Test title',
            pub_date=dj_timezone.now(),
            updated=dj_timezone.now(),
        )

    def test_str_method(self):
        self.assertEqual(self.entry.__str__(), 'Testblog / Test title')

    def test_absolute_url_show(self):
        self.assertEqual(self.entry.get_absolute_url(), 'https://example.test/a1')

    def test_absolute_url_hide(self):
        self.assertEqual(
            self.entry.get_absolute_url('hide'),
            f'http://planet.{settings.BASE_DOMAIN_NAME}/hide/{self.entry.id}/',
        )
