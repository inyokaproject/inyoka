#-*- coding: utf-8 -*-
"""
    inyoka.utils.tests.test_slug
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from django.conf import settings
from django.test import TestCase
from inyoka.forum.models import Forum, Topic
from inyoka.portal.user import User
from inyoka.utils.database import _strip_ending_nums, find_next_increment


class TestUtilsSlug(TestCase):
    def setUp(self):
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
        # validate inyoka.utils.database._strip_ending_nums

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
