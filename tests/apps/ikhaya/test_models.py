#-*- coding: utf-8 -*-
"""
    tests.apps.ikhaya.test_models
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test Ikhaya models.

    :copyright: (c) 2011-2014 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from datetime import date, time, timedelta

from django.conf import settings
from django.test import TestCase

from inyoka.utils.urls import url_for
from inyoka.portal.user import User
from inyoka.ikhaya.models import Article, Category, Event, Suggestion


class TestArticleModel(TestCase):

    def setUp(self):
        self.user = User.objects.register_user('admin', 'admin', 'admin',
                False)

        self.category1 = Category.objects.create(name='Test Category')
        self.category2 = Category.objects.create(name='Test Category')

        self.article1 = Article(pub_date=date(2008, 7, 18), text='Text 1',
                pub_time=time(1, 33, 7), author=self.user, subject='Article',
                category=self.category1, intro='Intro 1')
        self.article1.save()

        self.article2 = Article(pub_date=date(2008, 7, 18), text="'''Text 2'''",
                pub_time=time(0, 0, 0), author=self.user, subject='Article',
                category=self.category2, intro='Intro 2')
        self.article2.save()

        self.article3 = Article(pub_date=date(2009, 4, 1), text='<a>Text 3</a>',
                pub_time=time(12, 34, 56), author=self.user,
                subject='Article', category=self.category1, intro='Intro 3',
                is_xhtml=True)
        self.article3.save()

    def test_automatic_slugs(self):
        self.assertEqual(self.category1.slug, 'test-category')
        self.assertEqual(self.category2.slug, 'test-category-2')

        self.assertEqual(self.article1.slug, 'article')
        self.assertEqual(self.article1.stamp, '2008/07/18')

        self.assertEqual(self.article2.slug, 'article-2')
        self.assertEqual(self.article2.stamp, '2008/07/18')

        self.assertEqual(self.article3.slug, 'article')
        self.assertEqual(self.article3.stamp, '2009/04/01')

    def test_simplify_xhtml(self):
        self.assertEqual(self.article3.simplified_text, 'Text 3')

    def test_simplify_wiki_markup(self):
        self.assertEqual(self.article2.simplified_text, 'Text 2')

    def test_simplify_does_strip(self):
        _old_text = self.article1.text
        self.article1.text = 'Text 1   '
        self.assertEqual(self.article1.simplified_text, 'Text 1')
        self.article1.text = _old_text


class TestCategoryModel(TestCase):

    def test_default_ordering(self):
        """Order categories by name -- Ticket #906"""
        names = [
            'Maecenas ut leo',
            'Phasellus lobortis felis',
            'Duis eget odio pulvinar',
            'Quisque volutpat'
        ]
        for name in names:
            Category.objects.create(name=name)
        self.assertEqual(
            list(Category.objects.values_list('name', flat=True).all()),
            sorted(names)
        )


class TestSuggestionModel(TestCase):

    def setUp(self):
        self.user = User.objects.register_user('admin', 'admin', 'admin',
            False)
        self.suggestion1 = Suggestion(author=self.user)
        self.suggestion1.save()

    def test_url(self):
        url = 'http://ikhaya.{0}/suggestions/#{1}'.format(settings.BASE_DOMAIN_NAME, self.suggestion1.id)
        self.assertEqual(url_for(self.suggestion1), url)


class TestEventModel(TestCase):

    def setUp(self):
        self.user = User.objects.register_user('admin', 'admin', 'admin',
            False)

    # Negative parameters will not be tested because this would be
    # an invalid usage.

    def test_upcoming_getZero_isEmpty_returnNone(self):
        self.assertEqual(list(Event.objects.get_upcoming(0)), [])

    def test_upcoming_getOne_isEmpty_returnNone(self):
        self.assertEqual(list(Event.objects.get_upcoming(1)), [])

    def test_upcoming_getZero_oneVisibleEvent_returnNone(self):
        Event.objects.create(name='Event', date=date.today(),
            author=self.user, visible=True)
        self.assertEqual(list(Event.objects.get_upcoming(0)), [])

    def test_upcoming_getOne_oneVisibleEvent_returnEvent(self):
        event = Event.objects.create(name='Event', date=date.today(),
            author=self.user, visible=True)
        self.assertEqual(list(Event.objects.get_upcoming(1)), [event])

    def test_upcoming_getMoreThanInside_oneVisibleEvent_returnEvent(self):
        event = Event.objects.create(name='Event', date=date.today(),
            author=self.user, visible=True)
        self.assertEqual(list(Event.objects.get_upcoming(2)), [event])

    def test_upcoming_getZero_oneInvisibleEvent_returnNone(self):
        Event.objects.create(name='Event', date=date.today(),
            author=self.user, visible=False)
        self.assertEqual(list(Event.objects.get_upcoming(0)), [])

    def test_upcoming_getOne_oneInvisibleEvent_returnNone(self):
        Event.objects.create(name='Event', date=date.today(),
            author=self.user, visible=False)
        self.assertEqual(list(Event.objects.get_upcoming(1)), [])

    def test_upcoming_getMoreThanInside_oneInvisibleEvent_returnNone(self):
        Event.objects.create(name='Event', date=date.today(),
            author=self.user, visible=False)
        self.assertEqual(list(Event.objects.get_upcoming(2)), [])

    def test_upcoming_getDefault_returnCorrectNumEvents(self):
        events = [Event.objects.create(name='Event %d' % i, date=date.today(), 
            author=self.user, visible=True) for i in range(10)]
        Event.objects.create(name='Event not listed', date=date.today(),
            author=self.user, visible=True)
        self.assertEqual(list(Event.objects.get_upcoming()), events)

    def test_upcomingDate_startYesterday_returnNone(self):
        Event.objects.create(name='Event',
            date=date.today()+timedelta(days=-1),
            author=self.user, visible=True)
        self.assertEqual(list(Event.objects.get_upcoming()), [])

    def test_upcomingDate_startToday_returnEvent(self):
        event = Event.objects.create(name='Event',
            date=date.today()+timedelta(days=0),
            author=self.user, visible=True)
        self.assertEqual(list(Event.objects.get_upcoming()), [event])

    def test_upcomingDate_startTomorrow_returnEvent(self):
        event = Event.objects.create(name='Event',
            date=date.today()+timedelta(days=1),
            author=self.user, visible=True)
        self.assertEqual(list(Event.objects.get_upcoming()), [event])

    def test_upcomingDate_startYesterdayEndYesterday_returnNone(self):
        Event.objects.create(name='Event',
            date=date.today()+timedelta(days=-1),
            enddate=date.today()+timedelta(days=-1),
            author=self.user, visible=True)
        self.assertEqual(list(Event.objects.get_upcoming()), [])

    def test_upcoming_getLessThanInside_severalEvents_returnCorrectNumber(self):
        event1 = Event.objects.create(name='Event1', date=date.today(),
            author=self.user, visible=True)
        event2 = Event.objects.create(name='Event2', date=date.today(),
            author=self.user, visible=True)
        Event.objects.create(name='Event3', date=date.today(),
            author=self.user, visible=True)
        self.assertEqual(list(Event.objects.get_upcoming(2)), [event1,event2])

    def test_upcomingDate_startYesterdayEndToday_returnEvent(self):
        event = Event.objects.create(name='Event',
            date=date.today()+timedelta(days=-1),
            enddate=date.today()+timedelta(days=0),
            author=self.user, visible=True)
        self.assertEqual(list(Event.objects.get_upcoming()), [event])

    def test_upcomingDate_startYesterdayEndTomorrow_returnEvent(self):
        event = Event.objects.create(name='Event',
            date=date.today()+timedelta(days=-1),
            enddate=date.today()+timedelta(days=1),
            author=self.user, visible=True)
        self.assertEqual(list(Event.objects.get_upcoming()), [event])

    def test_upcomingDate_startTodayEndToday_returnEvent(self):
        event = Event.objects.create(name='Event',
            date=date.today()+timedelta(days=0),
            enddate=date.today()+timedelta(days=0),
            author=self.user, visible=True)
        self.assertEqual(list(Event.objects.get_upcoming()), [event])

    def test_upcomingDate_startTodayEndTomorrow_returnEvent(self):
        event = Event.objects.create(name='Event',
            date=date.today()+timedelta(days=0),
            enddate=date.today()+timedelta(days=1),
            author=self.user, visible=True)
        self.assertEqual(list(Event.objects.get_upcoming()), [event])

    def test_upcomingDate_startTomorrowEndTomorrow_returnEvent(self):
        event = Event.objects.create(name='Event',
            date=date.today()+timedelta(days=1),
            enddate=date.today()+timedelta(days=1),
            author=self.user, visible=True)
        self.assertEqual(list(Event.objects.get_upcoming()), [event])

    def test_upcomingDateUnordered_getDefault_returnCorrectOrder(self):
        event1 = Event.objects.create(name='Event1',
            date=date.today()+timedelta(days=2),
            author=self.user, visible=True)
        event2 = Event.objects.create(name='Event2',
            date=date.today()+timedelta(days=3),
            author=self.user, visible=True)
        event3 = Event.objects.create(name='Event3',
            date=date.today()+timedelta(days=1),
            author=self.user, visible=True)
        self.assertEqual(list(Event.objects.get_upcoming()),
            [event3,event1,event2])
