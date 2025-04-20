"""
    tests.apps.planet.test_models
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test planet models.

    :copyright: (c) 2012-2025 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
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
            'testing',
            'example@example.com',
            'pwd', False)

    def test_delete_user__preserves_blog_via_protected_error(self):
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

        with self.assertRaisesMessage(ProtectedError,
                                      "Cannot delete some instances of model 'User' because they are referenced through protected foreign keys: 'Blog.user'."):
            self.user.delete()

        self.assertEqual(Blog.objects.count(), 1)
        self.assertEqual(BlogEntry.objects.count(), 1)
