"""
tests.apps.forum.test_migrations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test forum migrations.

:copyright: (c) 2024-2025 by the Inyoka Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from datetime import datetime, timedelta, timezone

from django_test_migrations.contrib.unittest_case import MigratorTestCase


class TestForumAdjustDatetime(MigratorTestCase):
    migrate_from = ('forum', '0018_add_index__topic_slug')
    migrate_to = ('forum', '0019_adjust_datetimes')

    def prepare(self):
        """Prepare some data before the migration."""
        user_model = self.old_state.apps.get_model('portal', 'User')
        user = user_model.objects.create(
            username='foo',
            email='foo@local.localhost',
        )

        forum_model = self.old_state.apps.get_model('forum', 'Forum')
        forum1 = forum_model.objects.create(name='Forum 1')

        topic_model = self.old_state.apps.get_model('forum', 'Topic')
        topic = topic_model.objects.create(
            title='A test Topic', author=user, forum=forum1
        )

        post_model = self.old_state.apps.get_model('forum', 'Post')
        post__cest = post_model.objects.create(
            text='Post 1',
            author=user,
            topic=topic,
            position=0,
            pub_date=datetime(2023, 5, 26, 3, 34, 54, tzinfo=timezone.utc),
        )
        self.post_id__cest = post__cest.id

        post__cet = post_model.objects.create(
            text='Post 2',
            author=user,
            topic=topic,
            position=1,
            pub_date=datetime(2024, 1, 16, 21, 57, 1, tzinfo=timezone.utc),
        )
        self.post_id__cet = post__cet.id


        revision_model = self.old_state.apps.get_model('forum', 'PostRevision')
        revision = revision_model.objects.create(
            text='Post 2 revision',
            post=post__cet,
            store_date=datetime(2014, 1, 10, 10, 5, 1, tzinfo=timezone.utc),
        )
        self.revision_id = revision.id


        poll_model = self.old_state.apps.get_model('forum', 'Poll')
        poll_no_end = poll_model.objects.create(
            question='quo vadis?',
            start_time=datetime(2024, 1, 1, 11, 24, 29, tzinfo=timezone.utc),
            topic=topic
        )
        self.poll_no_end_id = poll_no_end.id

        poll_with_end = poll_model.objects.create(
            question='quo vadis 2?',
            start_time=datetime(2024, 1, 1, 11, 24, 29, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 8, 11, 24, 29, tzinfo=timezone.utc),
            topic=topic,
        )
        self.poll_with_end_id = poll_with_end.id

    def test_post_pub_date(self):
        post_model = self.new_state.apps.get_model('forum', 'Post')

        with self.subTest('CEST'):
            p = post_model.objects.get(id=self.post_id__cest)
            self.assertEqual(
                p.pub_date, datetime(2023, 5, 26, 5, 34, 54, tzinfo=timezone.utc)
            )
            self.assertEqual(
                p.pub_date,
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
            p = post_model.objects.get(id=self.post_id__cet)
            self.assertEqual(
                p.pub_date, datetime(2024, 1, 16, 22, 57, 1, tzinfo=timezone.utc)
            )
            self.assertEqual(
                p.pub_date,
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

    def test_poll_datetimes(self):
        poll_model = self.new_state.apps.get_model('forum', 'Poll')
        with self.subTest('no end'):
            poll = poll_model.objects.get(id=self.poll_no_end_id)
            self.assertEqual(poll.start_time,
                             datetime(2024, 1, 1, 13, 24, 29, tzinfo=timezone(timedelta(seconds=3600), 'CET')))
            self.assertIsNone(poll.end_time)

        with self.subTest('with end'):
            poll = poll_model.objects.get(id=self.poll_with_end_id)
            self.assertEqual(poll.start_time,
                             datetime(2024, 1, 1, 13, 24, 29,
                                      tzinfo=timezone(timedelta(seconds=3600), 'CET')))
            self.assertEqual(poll.end_time,
                             datetime(2024, 1, 8, 13, 24, 29,
                                      tzinfo=timezone(timedelta(seconds=3600), 'CET')))

    def test_revision_datetime(self):
        revision_model = self.new_state.apps.get_model('forum', 'PostRevision')

        self.assertEqual(revision_model.objects.count(), 1)

        r = revision_model.objects.get(id=self.revision_id)
        self.assertEqual(r.store_date, datetime(2014, 1, 10, 11, 5, 1, tzinfo=timezone.utc))
