"""
    tests.utils.test_slug
    ~~~~~~~~~~~~~~~~~~~~~

    Test for slug uniqueness and slug numberation

    :copyright: (c) 2007-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from inyoka.forum.models import Forum, Topic
from inyoka.portal.user import User
from inyoka.utils.database import _strip_ending_nums
from inyoka.utils.test import TestCase


class TestUtilsSlug(TestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.register_user('slugadmin', 'slugadmin', 'slugadmin', False)

        # creating forums
        self.forum1 = Forum(name='This is a test forum')
        self.forum1.save()

        self.forum2 = Forum(name='This is a test forum')
        self.forum2.save()

        self.forum3 = Forum(name='This is a test forum')
        self.forum3.save()

        # creating topics
        self.topic1 = Topic(title='This is a test topic', author=self.user,
                forum=self.forum1)
        self.topic1.save()

        self.topic2 = Topic(title='This is a test topic', author=self.user,
                forum=self.forum2)
        self.topic2.save()

        self.topic3 = Topic(title='This is a test topic', author=self.user,
                forum=self.forum3)
        self.topic3.save()

        self.topic4 = Topic(title='a', author=self.user,
                forum=self.forum3)
        self.topic4.save()

        self.topic5 = Topic(title='apo', author=self.user,
                forum=self.forum3)
        self.topic5.save()

        self.topic6 = Topic(title='a', author=self.user,
                forum=self.forum3)
        self.topic6.save()

        self.topic7 = Topic(title='Erwartungen an ubuntuusers.de wurden nicht erfüllt',
                author=self.user, forum=self.forum1)
        self.topic7.save()

        self.topic8 = Topic(title='Erwartungen an ubuntuusers.de wurden nicht erfüllt',
                author=self.user, forum=self.forum1)
        self.topic8.save()

    def test_ending_nums(self):
        map = [
            ('test', 'test'),
            ('test-1', 'test'),
            ('test-12', 'test'),
            ('longer-test', 'longer-test'),
            ('longer-test-1', 'longer-test'),
            ('longer-test-12', 'longer-test'),
            ('even-more-longer-test', 'even-more-longer-test'),
            ('even-more-longer-test-1', 'even-more-longer-test'),
            ('even-more-longer-test-12', 'even-more-longer-test'),
        ]

        for given, needed in map:
            self.assertEqual(_strip_ending_nums(given), needed)

    def test_unique_slug(self):
        self.assertEqual(self.forum1.slug, 'this-is-a-test-forum')
        self.assertEqual(self.forum2.slug, 'this-is-a-test-forum-2')
        self.assertEqual(self.forum3.slug, 'this-is-a-test-forum-3')

        self.assertEqual(self.topic1.slug, 'this-is-a-test-topic')
        self.assertEqual(self.topic2.slug, 'this-is-a-test-topic-2')
        self.assertEqual(self.topic3.slug, 'this-is-a-test-topic-3')

        self.assertEqual(self.topic4.slug, 'a')
        self.assertEqual(self.topic5.slug, 'apo')
        self.assertEqual(self.topic6.slug, 'a-2')

        self.assertEqual(self.topic7.slug, 'erwartungen-an-ubuntuusers-de-wurden-nicht-erf')
        self.assertEqual(self.topic8.slug, 'erwartungen-an-ubuntuusers-de-wurden-nicht-erf-2')

        # Make sure slugs aren't longer than 50 chars, sqlite testsuite won't pick that up
        self.assertTrue(len(self.topic7.slug) <= 50)
        self.assertTrue(len(self.topic8.slug) <= 50)
