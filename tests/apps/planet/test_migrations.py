"""
tests.apps.planet.test_migrations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test planet migrations.

:copyright: (c) 2024-2025 by the Inyoka Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from datetime import datetime, timezone

from django_test_migrations.contrib.unittest_case import MigratorTestCase


class TestPlanetAdjustDatetime(MigratorTestCase):
    migrate_from = ('planet', '0005_auto_20191027_1814')
    migrate_to = ('planet', '0006_adjust_datetimes')

    def prepare(self):
        """Prepare some data before the migration."""
        user_model = self.old_state.apps.get_model('portal', 'User')
        user = user_model.objects.create(
            username='foo',
            email='foo@local.localhost',
        )

        blog_model = self.old_state.apps.get_model('planet', 'Blog')
        blog = blog_model.objects.create(
            name='Blog',
            blog_url='http://blog.test/',
            feed_url='http://feed.test/',
            user=user,
            last_sync=datetime(2025, 5, 26, 7, 40, 54, tzinfo=timezone.utc),
        )
        self.blog_id = blog.id

        entry_model = self.old_state.apps.get_model('planet', 'Entry')
        entry = entry_model.objects.create(
            blog=blog,
            guid='guid-blog-entry1',
            title='Entry 1',
            url='http://entry.test/',
            text='Entry 1 text',
            pub_date=datetime(2025, 1, 2, 10, 34, 4, tzinfo=timezone.utc),
            updated=datetime(2025, 5, 26, 7, 31, 5, tzinfo=timezone.utc),
            author='Author',
        )
        self.entry_id = entry.id

    def test_pub_date(self):
        blog_model = self.new_state.apps.get_model('planet', 'Blog')
        blog = blog_model.objects.get(id=self.blog_id)
        self.assertEqual(
            blog.last_sync, datetime(2025, 5, 26, 9, 40, 54, tzinfo=timezone.utc)
        )

        entry_model = self.new_state.apps.get_model('planet', 'Entry')
        e = entry_model.objects.get(id=self.entry_id)
        self.assertEqual(
            e.pub_date, datetime(2025, 1, 2, 11, 34, 4, tzinfo=timezone.utc)
        )
        self.assertEqual(
            e.updated, datetime(2025, 5, 26, 9, 31, 5, tzinfo=timezone.utc)
        )
