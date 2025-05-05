"""
tests.apps.wiki.test_migrations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test wiki migrations.

:copyright: (c) 2023-2025 by the Inyoka Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

import datetime
from hashlib import sha1

from django_test_migrations.contrib.unittest_case import MigratorTestCase


class TestRevisionAdjustDatetime(MigratorTestCase):
    migrate_from = ('wiki', '0006_page_upper_page_name_idx')
    migrate_to = ('wiki', '0007_adjust_datetimes')

    def prepare(self):
        """Prepare some data before the migration."""
        user_model = self.old_state.apps.get_model('portal', 'User')
        user = user_model.objects.create(
            username='foo',
            email='foo@local.localhost',
        )

        page_model = self.old_state.apps.get_model('wiki', 'Page')
        revision_model = self.old_state.apps.get_model('wiki', 'Revision')
        text_model = self.old_state.apps.get_model('wiki', 'Text')
        p = page_model(
            name='foo',
        )

        text = text_model.objects.create(value='foo text')
        p.save()
        p.rev = revision_model(
            page=p,
            text=text,
            user=user,
            change_date=datetime.datetime(
                2023, 5, 26, 3, 34, 54, tzinfo=datetime.timezone.utc
            ),
            note='Created',
        )
        p.rev.save()
        p.last_rev = p.rev
        p.save()

        self.page_id = p.id

    def test_revision_change_date(self):
        page_model = self.new_state.apps.get_model('wiki', 'Page')

        revision = page_model.objects.get(id=self.page_id).last_rev
        self.assertEqual(
            revision.change_date,
            datetime.datetime(2023, 5, 26, 5, 34, 54, tzinfo=datetime.timezone.utc),
        )
        self.assertEqual(
            revision.change_date,
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

class TestWikiIndexCreation(MigratorTestCase):
    migrate_from = ('wiki', '0007_adjust_datetimes')
    migrate_to = ('wiki', '0008_create_wiki_index')

    def test_wiki_index_new(self):
        page_model = self.new_state.apps.get_model('wiki', 'Page')
        self.assertEqual(page_model.objects.count(), 1)

        p = page_model.objects.get(name__iexact='Wiki/Index')
        self.assertEqual(p.last_rev.text.value, '[[PageList()]]')


class TestWikiIndexExistingUntouched(MigratorTestCase):
    migrate_from = ('wiki', '0007_adjust_datetimes')
    migrate_to = ('wiki', '0008_create_wiki_index')

    def prepare(self):
        """Prepare some data before the migration."""
        user_model = self.old_state.apps.get_model('portal', 'User')
        user = user_model.objects.create(
            username='foo',
            email='foo@local.localhost',
        )

        page_model = self.old_state.apps.get_model('wiki', 'Page')
        revision_model = self.old_state.apps.get_model('wiki', 'Revision')
        text_model = self.old_state.apps.get_model('wiki', 'Text')
        p = page_model(
            name='Wiki/Index',
        )
        p.save()

        value = 'foobar'
        text = text_model.objects.create(value=value,
                                         hash=sha1(value.encode('utf-8')).hexdigest())

        p.rev = revision_model(
            page=p,
            text=text,
            user=user,
            change_date=datetime.datetime(2025, 5, 2, 7, 34, 50, tzinfo=datetime.timezone.utc),
            note='manual init',
        )
        p.rev.save()
        p.last_rev = p.rev
        p.save()

        self.page_id = p.id

    def test_wiki_index_preexisting(self):
        page_model = self.new_state.apps.get_model('wiki', 'Page')
        self.assertEqual(page_model.objects.count(), 1)

        revision_model = self.new_state.apps.get_model('wiki', 'Revision')
        self.assertEqual(revision_model.objects.count(), 1)

        p = page_model.objects.get(name__iexact='Wiki/Index')
        self.assertEqual(p.id, self.page_id)
        self.assertEqual(p.last_rev.text.value, 'foobar')
