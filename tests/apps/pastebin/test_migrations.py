"""
tests.apps.pastebin.test_migrations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test pastebin migrations.

:copyright: (c) 2024-2025 by the Inyoka Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from datetime import datetime, timedelta, timezone

from django_test_migrations.contrib.unittest_case import MigratorTestCase


class TestPastebinEntryAdjustDatetime(MigratorTestCase):
    migrate_from = ('pastebin', '0008_alter_entry_pub_date')
    migrate_to = ('pastebin', '0009_adjust_datetimes')

    def prepare(self):
        """Prepare some data before the migration."""
        user_model = self.old_state.apps.get_model('portal', 'User')
        user = user_model.objects.create(
            username='foo',
            email='foo@local.localhost',
        )

        entry_model = self.old_state.apps.get_model('pastebin', 'Entry')
        entry__cest = entry_model.objects.create(
            title='1',
            author=user,
            lang='C',
            code='int main() { exit(0);}',
            pub_date=datetime(2023, 5, 26, 3, 34, 54, tzinfo=timezone.utc),
        )
        self.entry_id__cest = entry__cest.id

        entry__cet = entry_model.objects.create(
            title='1',
            author=user,
            lang='C',
            code='int main() { exit(0);}',
            pub_date=datetime(2024, 1, 16, 21, 57, 1, tzinfo=timezone.utc),
        )
        self.entry_id__cet = entry__cet.id

    def test_entry_pub_date(self):
        entry_model = self.new_state.apps.get_model('pastebin', 'Entry')

        with self.subTest('CEST'):
            e = entry_model.objects.get(id=self.entry_id__cest)
            self.assertEqual(
                e.pub_date, datetime(2023, 5, 26, 5, 34, 54, tzinfo=timezone.utc)
            )
            self.assertEqual(
                e.pub_date,
                datetime(
                    2023,
                    5,
                    26,
                    7,
                    34,
                    54,
                    tzinfo=timezone(timedelta(seconds=7200), 'CEST'),
                ),
            )

        with self.subTest('CET'):
            e = entry_model.objects.get(id=self.entry_id__cet)
            self.assertEqual(
                e.pub_date, datetime(2024, 1, 16, 22, 57, 1, tzinfo=timezone.utc)
            )
            self.assertEqual(
                e.pub_date,
                datetime(
                    2024,
                    1,
                    16,
                    23,
                    57,
                    1,
                    tzinfo=timezone(timedelta(seconds=3600), 'CET'),
                ),
            )
