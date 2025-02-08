"""
    tests.apps.portal.test_migrations
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test portal migrations.

    :copyright: (c) 2023-2025 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import datetime

from django_test_migrations.contrib.unittest_case import MigratorTestCase


class TestArticalePublicationMerge(MigratorTestCase):
    migrate_from = ("ikhaya", "0010_auto_20230312_1704")
    migrate_to = ("ikhaya", "0011_article_publication_datetime")

    def prepare(self):
        """Prepare some data before the migration."""
        User = self.old_state.apps.get_model("portal", "User")
        author = User.objects.create(
            username="foo", email="foo@local.localhost",
        )

        Category = self.old_state.apps.get_model("ikhaya", "Category")
        category = Category.objects.create(name='Test Category')

        Article = self.old_state.apps.get_model("ikhaya", "Article")
        self.a = Article.objects.create(
            pub_date="2024-01-01",
            pub_time="10:00:00",
            intro='Intro 1',
            text='Text 1',
            subject='Article',
            category=category,
            author=author,
        )

        self.a2 = Article.objects.create(
            pub_date="2023-05-15",
            pub_time="23:00",
            intro='Intro ',
            text='Text 2',
            subject='Article2',
            category=category,
            author=author,
        )

    def test_publication_datetime(self):
        Article = self.new_state.apps.get_model("ikhaya", "Article")
        a = Article.objects.get(pk=self.a.pk)

        self.assertEqual(a.publication_datetime,
                         datetime.datetime(2024, 1, 1, 10, 0, tzinfo=datetime.timezone.utc))

    def test_publication_datetime__second_article(self):
        Article = self.new_state.apps.get_model("ikhaya", "Article")
        a = Article.objects.get(pk=self.a2.pk)

        self.assertEqual(a.publication_datetime,
                         datetime.datetime(2023, 5, 15, 23, 0, tzinfo=datetime.timezone.utc))
