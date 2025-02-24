"""
    tests.apps.ikhaya.test_migrations
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test ikhaya migrations.

    :copyright: (c) 2023-2025 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import datetime

from django_test_migrations.contrib.unittest_case import MigratorTestCase


class TestArticlePublicationMerge(MigratorTestCase):
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


class TestAdjustDatetime(MigratorTestCase):
    migrate_from = ('ikhaya', '0011_article_publication_datetime')
    migrate_to = ('ikhaya', '0012_adjust_datetimes')

    def prepare(self):
        """Prepare some data before the migration."""
        user_model = self.old_state.apps.get_model('portal', 'User')
        user = user_model.objects.create(
            username='foo',
            email='foo@local.localhost',
        )

        category_model = self.old_state.apps.get_model("ikhaya", "Category")
        category = category_model.objects.create(name='Test Category')

        article_model = self.old_state.apps.get_model("ikhaya", "Article")
        a = article_model.objects.create(
            intro='Intro 1',
            text='Text 1',
            subject='Article',
            category=category,
            author=user,
            publication_datetime=datetime.datetime(2023, 5, 26, 3, 34, 54,
                                                   tzinfo=datetime.timezone.utc),
            updated=datetime.datetime(2023, 5, 26, 3, 34, 54,
                                      tzinfo=datetime.timezone.utc),
        )
        self.a_id = a.id
        a2 = article_model.objects.create(
            intro='Intro 2',
            text='Text 2',
            subject='Article2',
            category=category,
            author=user,
            publication_datetime=datetime.datetime(2023, 5, 25, 3, 34, 54, tzinfo=datetime.timezone.utc),
            updated=datetime.datetime(2023, 5, 25, 1, 34, 54,
                                                   tzinfo=datetime.timezone.utc),
        )
        self.a2_id = a2.id

        comment_model = self.old_state.apps.get_model('ikhaya', 'Comment')
        comment__cest = comment_model.objects.create(
            article=a,
            text='Comment 1',
            author=user,
            pub_date=datetime.datetime(2023, 5, 26, 3, 34, 54, tzinfo=datetime.timezone.utc),
        )
        self.comment_id__cest = comment__cest.id

        comment__cet = comment_model.objects.create(
            article=a,
            text='Comment 1',
            author=user,
            pub_date=datetime.datetime(2024, 1, 16, 21, 57, 1, tzinfo=datetime.timezone.utc),
        )
        self.comment_id__cet = comment__cet.id

        report_model = self.old_state.apps.get_model('ikhaya', 'Report')
        report = report_model.objects.create(
            article=a,
            text='Report 1',
            author=user,
            pub_date=datetime.datetime(2023, 4, 16, 5, 27, tzinfo=datetime.timezone.utc)
        )
        self.report_id = report.id

    def test_comment_pub_date(self):
        comment_model = self.new_state.apps.get_model('ikhaya', 'Comment')

        with self.subTest('CEST'):
            c = comment_model.objects.get(id=self.comment_id__cest)
            self.assertEqual(
                c.pub_date, datetime.datetime(2023, 5, 26, 5, 34, 54, tzinfo=datetime.timezone.utc)
            )
            self.assertEqual(
                c.pub_date,
                datetime.datetime(
                    2023,
                    5,
                    26,
                    7,
                    34,
                    54,
                    tzinfo=datetime.timezone(datetime.timedelta(seconds=7200), 'CEST'),
                ),
            )

        with self.subTest('CET'):
            c = comment_model.objects.get(id=self.comment_id__cet)
            self.assertEqual(
                c.pub_date, datetime.datetime(2024, 1, 16, 22, 57, 1, tzinfo=datetime.timezone.utc)
            )
            self.assertEqual(
                c.pub_date,
                datetime.datetime(
                    2024,
                    1,
                    16,
                    23,
                    57,
                    1,
                    tzinfo=datetime.timezone(datetime.timedelta(seconds=3600), 'CET'),
                ),
            )

    def test_report_pub_date(self):
        report_model = self.new_state.apps.get_model('ikhaya', 'Report')
        r = report_model.objects.get(id=self.report_id)
        self.assertEqual(r.pub_date,
                         datetime.datetime(2023, 4, 16, 9, 27, tzinfo=datetime.timezone(datetime.timedelta(seconds=7200), 'CEST')))

    def test_article_publication_date(self):
        article_model = self.new_state.apps.get_model('ikhaya', 'Article')
        a = article_model.objects.get(id=self.a_id)
        # publication_datetime should be the same
        self.assertEqual(a.publication_datetime,
                         datetime.datetime(2023, 5, 26, 3, 34, 54,
                                           tzinfo=datetime.timezone.utc))
        self.assertEqual(a.updated,
                         datetime.datetime(2023, 5, 26, 5, 34, 54,
                                           tzinfo=datetime.timezone.utc))

        a2 = article_model.objects.get(id=self.a2_id)
        self.assertEqual(a2.publication_datetime, datetime.datetime(2023, 5, 25, 3, 34, 54, tzinfo=datetime.timezone.utc))
        self.assertIsNone(a2.updated)
