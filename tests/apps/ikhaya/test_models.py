"""
    tests.apps.ikhaya.test_models
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test Ikhaya models.

    :copyright: (c) 2011-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from datetime import date, datetime, time, timedelta, UTC

import freezegun
from django.conf import settings

from inyoka.ikhaya.models import Article, Category, Comment, Event, Suggestion
from inyoka.portal.models import StaticFile
from inyoka.portal.user import User
from inyoka.utils.test import TestCase
from inyoka.utils.urls import url_for


class TestArticleModel(TestCase):

    def setUp(self):
        super().setUp()
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

    def test_get_text(self):
        # article2.is_xhtml = False
        self.assertEqual(
            self.article2.get_text(),
            '<p><strong>Text 2</strong></p>',
        )

        # article3.is_xhtml = True
        self.assertEqual(
            self.article3.get_text(),
            '<a>Text 3</a>',
        )

    def test_save__change_slug(self):
        self.article1.slug = 'test-article'
        self.article1.save()

        self.article1.refresh_from_db()
        self.assertEqual('test-article', self.article1.slug)

    def test_save__slug_stable(self):
        """Even if the subject is changed, the slug is still the same"""
        self.article1.subject = 'b'
        self.article1.save()

        self.article1.refresh_from_db()
        self.assertEqual('b', self.article1.subject)
        self.assertEqual('article', self.article1.slug)

    def test_updated(self):
        self.assertEqual(datetime(2008, 7, 18, 1, 33, 7), self.article1.updated)

        self.article1.pub_date = date(2009, 7, 18)
        self.article1.save()

        self.article1.refresh_from_db()
        # updated should be now also in 2009, even if not explicitly changed
        self.assertEqual(datetime(2009, 7, 18, 1, 33, 7), self.article1.updated)

    def test_save_update__update_fields(self):
        """Almost the same as test_updated -- except that `save()` uses update_fields"""
        self.assertEqual(datetime(2008, 7, 18, 1, 33, 7), self.article1.updated)

        self.article1.pub_date = date(2009, 7, 18)
        self.article1.save(update_fields=["pub_date"])

        self.article1.refresh_from_db()
        # updated should be now also in 2009, even if not explicitly changed
        self.assertEqual(datetime(2009, 7, 18, 1, 33, 7), self.article1.updated)


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

    def test_save(self):
        category = Category(name='name')
        category.save()

        self.assertEqual(Category.objects.count(), 1)

        category = Category.objects.get()
        self.assertEqual(category.name, 'name')
        self.assertEqual(category.slug, 'name')

        category.name = 'b'
        category.save()
        category = Category.objects.get()
        self.assertEqual(category.name, 'b')
        self.assertEqual(category.slug, 'name')

    def test_save__update_fields(self):
        category = Category(name='name')
        category.save()

        self.assertEqual(Category.objects.count(), 1)

        category = Category.objects.get()
        self.assertEqual(category.name, 'name')
        self.assertEqual(category.slug, 'name')
        self.assertIsNone(category.icon)

        category.name = 'b'
        category.icon = StaticFile.objects.create(identifier='test_attachment.png')
        category.save(update_fields=['name'])

        category = Category.objects.get()
        self.assertEqual(category.name, 'b')
        self.assertEqual(category.slug, 'name')
        # still None as not included in update_fields
        self.assertIsNone(category.icon)


class TestSuggestionModel(TestCase):

    def setUp(self):
        super().setUp()
        self.user = User.objects.register_user('admin', 'admin', 'admin',
            False)
        self.suggestion1 = Suggestion(author=self.user)
        self.suggestion1.save()

    def test_url(self):
        url = f'http://ikhaya.{settings.BASE_DOMAIN_NAME}/suggestions/#{self.suggestion1.id}'
        self.assertEqual(url_for(self.suggestion1), url)


class TestEventModel(TestCase):

    def setUp(self):
        super().setUp()
        self.user = User.objects.register_user('admin', 'admin', 'admin',
            False)

    # Negative parameters will not be tested because this would be
    # an invalid usage.

    def test_upcoming_getZero_isEmpty_returnNone(self):
        self.assertEqual(list(Event.objects.get_upcoming(0)), [])

    def test_upcoming_getOne_isEmpty_returnNone(self):
        self.assertEqual(list(Event.objects.get_upcoming(1)), [])

    def test_upcoming_getZero_oneVisibleEvent_returnNone(self):
        Event.objects.create(name='Event', date=datetime.now(UTC).date(),
            author=self.user, visible=True)
        self.assertEqual(list(Event.objects.get_upcoming(0)), [])

    def test_upcoming_getOne_oneVisibleEvent_returnEvent(self):
        event = Event.objects.create(name='Event', date=datetime.now(UTC).date(),
            author=self.user, visible=True)
        self.assertEqual(list(Event.objects.get_upcoming(1)), [event])

    def test_upcoming_getMoreThanInside_oneVisibleEvent_returnEvent(self):
        event = Event.objects.create(name='Event', date=datetime.now(UTC).date(),
            author=self.user, visible=True)
        self.assertEqual(list(Event.objects.get_upcoming(2)), [event])

    def test_upcoming_getZero_oneInvisibleEvent_returnNone(self):
        Event.objects.create(name='Event', date=datetime.now(UTC).date(),
            author=self.user, visible=False)
        self.assertEqual(list(Event.objects.get_upcoming(0)), [])

    def test_upcoming_getOne_oneInvisibleEvent_returnNone(self):
        Event.objects.create(name='Event', date=datetime.now(UTC).date(),
            author=self.user, visible=False)
        self.assertEqual(list(Event.objects.get_upcoming(1)), [])

    def test_upcoming_getMoreThanInside_oneInvisibleEvent_returnNone(self):
        Event.objects.create(name='Event', date=datetime.now(UTC).date(),
            author=self.user, visible=False)
        self.assertEqual(list(Event.objects.get_upcoming(2)), [])

    def test_upcoming_getDefault_returnCorrectNumEvents(self):
        events = [Event.objects.create(name='Event %d' % i, date=datetime.now(UTC).date(),
            author=self.user, visible=True) for i in range(10)]
        Event.objects.create(name='Event not listed', date=datetime.now(UTC).date(),
            author=self.user, visible=True)
        self.assertEqual(list(Event.objects.get_upcoming()), events)

    def test_upcomingDate_startYesterday_returnNone(self):
        Event.objects.create(name='Event',
            date=datetime.now(UTC).date() + timedelta(days=-1),
            author=self.user, visible=True)
        self.assertEqual(list(Event.objects.get_upcoming()), [])

    def test_upcomingDate_startToday_returnEvent(self):
        event = Event.objects.create(name='Event',
            date=datetime.now(UTC).date() + timedelta(days=0),
            author=self.user, visible=True)
        self.assertEqual(list(Event.objects.get_upcoming()), [event])

    def test_upcomingDate_startTomorrow_returnEvent(self):
        event = Event.objects.create(name='Event',
            date=datetime.now(UTC).date() + timedelta(days=1),
            author=self.user, visible=True)
        self.assertEqual(list(Event.objects.get_upcoming()), [event])

    def test_upcomingDate_startYesterdayEndYesterday_returnNone(self):
        Event.objects.create(name='Event',
            date=datetime.now(UTC).date() + timedelta(days=-1),
            enddate=datetime.now(UTC).date() + timedelta(days=-1),
            author=self.user, visible=True)
        self.assertEqual(list(Event.objects.get_upcoming()), [])

    def test_upcoming_getLessThanInside_severalEvents_returnCorrectNumber(self):
        date = datetime.now(UTC).date()
        Event.objects.create(name='Event1', date=date,
            author=self.user, visible=True)
        Event.objects.create(name='Event2', date=date,
            author=self.user, visible=True)
        Event.objects.create(name='Event3', date=date,
            author=self.user, visible=True)
        self.assertEqual(len(Event.objects.get_upcoming(2)), 2)

    def test_upcomingDate_startYesterdayEndToday_returnEvent(self):
        event = Event.objects.create(name='Event',
            date=datetime.now(UTC).date() + timedelta(days=-1),
            enddate=datetime.now(UTC).date() + timedelta(days=0),
            author=self.user, visible=True)
        self.assertEqual(list(Event.objects.get_upcoming()), [event])

    def test_upcomingDate_startYesterdayEndTomorrow_returnEvent(self):
        event = Event.objects.create(name='Event',
            date=datetime.now(UTC).date() + timedelta(days=-1),
            enddate=datetime.now(UTC).date() + timedelta(days=1),
            author=self.user, visible=True)
        self.assertEqual(list(Event.objects.get_upcoming()), [event])

    def test_upcomingDate_startTodayEndToday_returnEvent(self):
        event = Event.objects.create(name='Event',
            date=datetime.now(UTC).date() + timedelta(days=0),
            enddate=datetime.now(UTC).date() + timedelta(days=0),
            author=self.user, visible=True)
        self.assertEqual(list(Event.objects.get_upcoming()), [event])

    def test_upcomingDate_startTodayEndTomorrow_returnEvent(self):
        event = Event.objects.create(name='Event',
            date=datetime.now(UTC).date() + timedelta(days=0),
            enddate=datetime.now(UTC).date() + timedelta(days=1),
            author=self.user, visible=True)
        self.assertEqual(list(Event.objects.get_upcoming()), [event])

    def test_upcomingDate_startTomorrowEndTomorrow_returnEvent(self):
        event = Event.objects.create(name='Event',
            date=datetime.now(UTC).date() + timedelta(days=1),
            enddate=datetime.now(UTC).date() + timedelta(days=1),
            author=self.user, visible=True)
        self.assertEqual(list(Event.objects.get_upcoming()), [event])

    def test_upcomingDateUnordered_getDefault_returnCorrectOrder(self):
        event1 = Event.objects.create(name='Event1',
            date=datetime.now(UTC).date() + timedelta(days=2),
            author=self.user, visible=True)
        event2 = Event.objects.create(name='Event2',
            date=datetime.now(UTC).date() + timedelta(days=3),
            author=self.user, visible=True)
        event3 = Event.objects.create(name='Event3',
            date=datetime.now(UTC).date() + timedelta(days=1),
            author=self.user, visible=True)
        self.assertEqual(list(Event.objects.get_upcoming()),
            [event3, event1, event2])

    def test__coordinates_url__no_coordinates(self):
        event = Event.objects.create(name='Event1',
                                     date=datetime.now(UTC).date(),
                                     author=self.user, visible=True,
                                     )

        self.assertIsNone(event.coordinates_url)

    def test__coordinates_url(self):
        event = Event.objects.create(name='Event1',
                                     date=datetime.now(UTC).date(),
                                     author=self.user, visible=True,
                                     location_long=13.37871,
                                     location_lat=52.5139
                                     )

        self.assertEqual('https://www.openstreetmap.org/?mlat=52.5139&mlon=13.37871', event.coordinates_url)


class TestComments(TestCase):
    def setUp(self):
        self.user = User.objects.register_user('admin', 'admin', 'admin', False)

        self.category1 = Category.objects.create(name='Test Category')
        self.category2 = Category.objects.create(name='Test Category')

        self.article1 = Article.objects.create(pub_date=date(2008, 7, 18), text='Text 1',
                                pub_time=time(1, 33, 7), author=self.user, subject='Article',
                                category=self.category1, intro='Intro 1')

        self.article2 = Article.objects.create(pub_date=date(2018, 7, 18), text="'''Text 2'''",
                                pub_time=time(1, 0, 0), author=self.user, subject='Article',
                                category=self.category2, intro='Intro 2')

        with freezegun.freeze_time('2024-01-01 12:12'):
            self.comment1 = Comment.objects.create(article=self.article1, text='Text', author=self.user,
                                                   pub_date=datetime.now(UTC))
            self.comment2 = Comment.objects.create(article=self.article1, text='Text2', author=self.user,
                                                   pub_date=datetime.now(UTC))

            self.comment3 = Comment.objects.create(article=self.article2, text='Text3', author=self.user,
                                                   pub_date=datetime.now(UTC))

    def test_position(self):
        self.assertEqual(self.comment1.position, 1)
        self.assertEqual(self.comment2.position, 2)

        # only comment on another article
        self.assertEqual(self.comment3.position, 1)
