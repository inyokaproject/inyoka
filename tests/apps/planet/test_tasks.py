"""
tests.apps.planet.test_tasks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test planet tasks.

:copyright: (c) 2023-2025 by the Inyoka Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

import datetime

from inyoka.planet.models import Blog, Entry
from inyoka.planet.tasks import _sync
from inyoka.portal.user import User
from inyoka.utils.test import TestCase


class TestSync(TestCase):
    def setUp(self):
        super().setUp()
        self.admin = User.objects.register_user('admin', 'admin', 'admin', False)

    def test_blog_sync(self):
        blog = Blog(
            name='Testblog',
            blog_url='http://example.com/',
            feed_url='https://www.rssboard.org/files/sample-rss-2.xml',
            user=self.admin,
            active=True,
        )
        blog.save()

        _sync()

        self.assertEqual(
            Entry.objects.count(), 4
        )  # has 5 entries, but only 4 with title

        e = Entry.objects.get(
            guid='http://www.nasa.gov/press-release/louisiana-students-to-hear-from-nasa-astronauts-aboard-space-station'
        )
        self.assertEqual(
            e.title,
            'Louisiana Students to Hear from NASA Astronauts Aboard Space Station',
        )
        self.assertEqual(
            e.url,
            'http://www.nasa.gov/press-release/louisiana-students-to-hear-from-nasa-astronauts-aboard-space-station',
        )
        self.assertEqual(
            e.text,
            "<p>As part of the state's first Earth-to-space call, students from Louisiana will have an opportunity soon to hear from NASA astronauts aboard the International Space Station.</p>",
        )
        self.assertEqual(
            e.pub_date,
            datetime.datetime(2023, 7, 21, 13, 4, tzinfo=datetime.timezone.utc),
        )
