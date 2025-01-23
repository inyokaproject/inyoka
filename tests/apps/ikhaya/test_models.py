"""
    tests.apps.ikhaya.test_models
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test Ikhaya models.

    :copyright: (c) 2011-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import zoneinfo
from datetime import datetime, timedelta, timezone

import freezegun
from django.conf import settings
from django.db import IntegrityError

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

        self.article1 = Article(
            publication_datetime=datetime(2008, 7, 18, 1, 33, 7, tzinfo=timezone.utc),
            text='Text 1',
            author=self.user,
            subject='Article',
            category=self.category1,
            intro='Intro 1'
        )
        self.article1.save()

        self.article2 = Article(
            publication_datetime=datetime(2008, 7, 18, 0, 0, 0, tzinfo=timezone.utc),
            text="'''Text 2'''",
            author=self.user,
            subject='Article',
            category=self.category2,
            intro='Intro 2'
        )
        self.article2.save()

        self.article3 = Article(
            publication_datetime=datetime(2009, 4, 1, 12, 34, 56, tzinfo=timezone.utc),
            text='<a>Text 3</a>',
            author=self.user,
            subject='Article',
            category=self.category1,
            intro='Intro 3',
            is_xhtml=True
        )
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

    def test_save__change_slug__invalid_characters(self):
        self.article1.slug = 'test articleß'
        self.article1.save()

        self.article1.refresh_from_db()
        self.assertEqual('test-articless', self.article1.slug)

    def test_save__slug(self):
        local_timezone = timezone(timedelta(seconds=7200))

        a = Article.objects.create(**{
            'publication_datetime': datetime(2008, 7, 18, 1, 33, 7,
                                             tzinfo=local_timezone),
            'text': 'foo',
            'author': self.user,
            'subject': 'Article',
            'category': self.category1,
            'intro': 'Intro',
        })
        a.refresh_from_db()
        self.assertEqual(a.stamp, '2008/07/17')

        # ideally this could be 'article' -- but as `find_next_increment` in
        # `Article.save` uses the local datetime, the postfix gets added
        self.assertEqual(a.slug, 'article-3')

        with self.subTest(case='slug not changed for uniqueness, if manually set'):
            a.slug = 'article'
            a.save()
            a.refresh_from_db()
            self.assertEqual(a.slug, 'article')

        with self.subTest(case='integrity error raised, if slug and publication datetime changed'), \
             self.assertRaisesMessage(IntegrityError,
                                      self._msg_unique_constraint('unique_pub_date_slug')):
            a.publication_datetime = self.article1.publication_datetime
            a.save()

    def test_save__slug_stable(self):
        """Even if the subject is changed, the slug is still the same"""
        self.article1.subject = 'b'
        self.article1.save()

        self.article1.refresh_from_db()
        self.assertEqual('b', self.article1.subject)
        self.assertEqual('article', self.article1.slug)

    def test_empty_text(self):
        with self.assertRaisesMessage(IntegrityError,
                                      self._msg_not_null_constraint('ikhaya_article', 'text')):
            Article.objects.create(
                publication_datetime=datetime(2008, 7, 18, 1, 33, 7,
                                              tzinfo=timezone.utc),
                text=None,
                author=self.user,
                subject='Article',
                category=self.category1,
                intro='Intro 1',
            )

    def test_empty_intro(self):
        with self.assertRaisesMessage(IntegrityError,
                                      self._msg_not_null_constraint('ikhaya_article', 'intro')):
            Article.objects.create(
                publication_datetime=datetime(2008, 7, 18, 1, 33, 7,
                                              tzinfo=timezone.utc),
                text='foo',
                author=self.user,
                subject='Article',
                category=self.category1,
                intro=None,
            )

    def test_unique_constraint__same_date_and_slug_raises_error(self):
        common_parameters = {
            'publication_datetime': datetime(2008, 7, 18, 1, 33, 7,
                                             tzinfo=timezone.utc),
            'text': 'foo',
            'author': self.user,
            'subject': 'Article',
            'category': self.category1,
            'intro': 'Intro',
            'slug': 'foo',
        }

        Article.objects.create(
            **common_parameters
        )

        with self.assertRaisesMessage(IntegrityError,
                                      self._msg_unique_constraint('unique_pub_date_slug')):
            Article.objects.create(
                **common_parameters
            )

    def test_unique_constraint__same_slug_different_days_works(self):
        common_parameters = {
            'publication_datetime': datetime(2008, 7, 18, 1, 33, 7,
                                             tzinfo=timezone.utc),
            'text': 'foo',
            'author': self.user,
            'subject': 'Article',
            'category': self.category1,
            'intro': 'Intro',
            'slug': 'foo',
        }

        Article.objects.create(
            **common_parameters
        )

        common_parameters['publication_datetime'] = datetime(2008, 7, 19, 1, 33, 7,
                                                             tzinfo=timezone.utc)
        Article.objects.create(**common_parameters)

    def test_unique_constraint__different_timezones(self):
        common_parameters = {
            'publication_datetime': datetime(2008, 7, 18, 1, 33, 7,
                                             tzinfo=timezone.utc),
            'text': 'foo',
            'author': self.user,
            'subject': 'Article',
            'category': self.category1,
            'intro': 'Intro',
            'slug': 'foo',
        }

        Article.objects.create(
            **common_parameters
        )

        common_parameters['publication_datetime'] = datetime(2008, 7, 18, 23, 33, 7,
                                                             tzinfo=timezone(timedelta(seconds=7200)))
        with self.assertRaisesMessage(IntegrityError,
                                      self._msg_unique_constraint('unique_pub_date_slug')):
            Article.objects.create(**common_parameters)

    def test_unique_constraint__different_dates_in_UTC(self):
        """
        Even if both articles have the same date in locale time,
        no integrity error will be raised. (as in UTC they have different dates)
        """
        local_timezone = timezone(timedelta(seconds=7200))

        common_parameters = {
            'publication_datetime': datetime(2010, 7, 18, 1, 33, 7,
                                             tzinfo=local_timezone),
            'text': 'foo',
            'author': self.user,
            'subject': 'Article',
            'category': self.category1,
            'intro': 'Intro',
            'slug': 'foo',
        }

        a = Article.objects.create(
            **common_parameters
        )
        a.refresh_from_db()
        self.assertEqual(a.stamp, '2010/07/17')

        common_parameters['publication_datetime'] = datetime(2010, 7, 18, 23, 33, 7,
                                                             tzinfo=local_timezone)

        a = Article.objects.create(**common_parameters)
        self.assertEqual(a.stamp, '2010/07/18')

    def test_stamp__no_utc_time_passed__still_returns_utc_date(self):
        """
        2010-07-1**8** 01:33:07+02:00
         is equal to
        2010-07-1**7** 23:33:07+00:00

        The stamp should be dated in UTC: 2010-07-17
        """
        self.article1.publication_datetime = datetime(2010, 7, 18, 1, 33, 7,
                                             tzinfo=timezone(timedelta(seconds=7200)))
        self.article1.save()

        self.assertEqual(self.article1.publication_datetime.tzinfo,
                         timezone(timedelta(seconds=7200)))
        self.assertEqual(self.article1.stamp, '2010/07/17')

        self.article1.refresh_from_db()

        # ORM will return in UTC
        self.assertEqual(self.article1.publication_datetime.tzinfo, timezone.utc)
        self.assertEqual(self.article1.stamp, '2010/07/17')

    def test_stamp_wrapping_time(self):
        self.article1.publication_datetime = datetime(2025, 1, 2, 23, 30, 44, tzinfo=timezone.utc)
        self.article1.save()

        self.article1.refresh_from_db()

        self.assertEqual(self.article1.stamp, '2025/01/02')
        self.assertEqual(self.article1.local_pub_datetime,
                         datetime(2025, 1, 3, 0, 30, 44,
                                  tzinfo=zoneinfo.ZoneInfo(key='Europe/Berlin')))

    def test_get_by_date_and_slug__wrapping_time(self):
        self.article1.publication_datetime = datetime(2025, 1, 2, 23, 30, 44,
                                                      tzinfo=timezone.utc)
        self.article1.save()

        with self.assertRaises(Article.DoesNotExist):
            Article.objects.get_by_date_and_slug(2025, 1, 3, self.article1.slug)

        Article.objects.get_by_date_and_slug(2025, 1, 2, self.article1.slug)


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

    def _create_one_event(self, visible=True):
        return Event.objects.create(name='Event',
                                    start=datetime.now(timezone.utc) + timedelta(minutes=12),
                                    end=datetime.now(timezone.utc) + timedelta(hours=12),
                                    author=self.user,
                                    visible=visible)

    def test_upcoming_getZero_isEmpty_returnNone(self):
        self.assertEqual(list(Event.objects.get_upcoming(0)), [])

    def test_upcoming_getOne_isEmpty_returnNone(self):
        self.assertEqual(list(Event.objects.get_upcoming(1)), [])

    def test_upcoming_getZero_oneVisibleEvent_returnNone(self):
        self._create_one_event()
        self.assertEqual(list(Event.objects.get_upcoming(0)), [])

    def test_upcoming_getOne_oneVisibleEvent_returnEvent(self):
        event = self._create_one_event()
        self.assertEqual(list(Event.objects.get_upcoming(1)), [event])

    def test_upcoming_getMoreThanInside_oneVisibleEvent_returnEvent(self):
        event = self._create_one_event()
        self.assertEqual(list(Event.objects.get_upcoming(2)), [event])

    def test_upcoming_getZero_oneInvisibleEvent_returnNone(self):
        self._create_one_event()
        self.assertEqual(list(Event.objects.get_upcoming(0)), [])

    def test_upcoming_getOne_oneInvisibleEvent_returnNone(self):
        self._create_one_event(visible=False)
        self.assertEqual(list(Event.objects.get_upcoming(1)), [])

    def test_upcoming_getMoreThanInside_oneInvisibleEvent_returnNone(self):
        self._create_one_event(visible=False)
        self.assertEqual(list(Event.objects.get_upcoming(2)), [])

    def test_upcoming_getDefault_returnCorrectNumEvents(self):
        events = [
            Event.objects.create(name='Event %d' % i,
                                 start=datetime.now(timezone.utc) + timedelta(hours=2),
                                 end=datetime.now(timezone.utc) + timedelta(hours=3),
                                 author=self.user, visible=True) for i in range(10)]
        Event.objects.create(name='Event not listed', start=datetime.now(timezone.utc),
                             end=datetime.now(timezone.utc),
                             author=self.user, visible=True)
        self.assertEqual(list(Event.objects.get_upcoming()), events)

    def test_upcomingDate_startYesterday_returnNone(self):
        Event.objects.create(name='Event',
            start=datetime.now(timezone.utc) + timedelta(days=-1),
            end=datetime.now(timezone.utc) + timedelta(days=-1),
            author=self.user, visible=True)
        self.assertEqual(list(Event.objects.get_upcoming()), [])

    def test_upcomingDate_startToday_returnEvent(self):
        event = Event.objects.create(name='Event',
            start=datetime.now(timezone.utc) + timedelta(seconds=10),
            end=datetime.now(timezone.utc),
            author=self.user, visible=True)
        self.assertEqual(list(Event.objects.get_upcoming()), [event])

    def test_upcomingDate_startTomorrow_returnEvent(self):
        event = Event.objects.create(name='Event',
            start=datetime.now(timezone.utc) + timedelta(days=1),
            end=datetime.now(timezone.utc) + timedelta(days=1),
            author=self.user, visible=True)
        self.assertEqual(list(Event.objects.get_upcoming()), [event])

    def test_upcomingDate_startYesterdayEndYesterday_returnNone(self):
        Event.objects.create(name='Event',
            start=datetime.now(timezone.utc) + timedelta(days=-1),
            end=datetime.now(timezone.utc) + timedelta(days=-1),
            author=self.user, visible=True)
        self.assertEqual(list(Event.objects.get_upcoming()), [])

    def test_upcoming_getLessThanInside_severalEvents_returnCorrectNumber(self):
        start = datetime.now(timezone.utc) + timedelta(minutes=5)
        Event.objects.create(name='Event1', start=start, end=start,
            author=self.user, visible=True)
        Event.objects.create(name='Event2', start=start, end=start,
            author=self.user, visible=True)
        Event.objects.create(name='Event3', start=start, end=start,
            author=self.user, visible=True)
        self.assertEqual(len(Event.objects.get_upcoming(2)), 2)

    def test_upcomingDate_startYesterdayEndToday_returnEvent(self):
        event = Event.objects.create(name='Event',
            start=datetime.now(timezone.utc) + timedelta(days=-1),
            end=datetime.now(timezone.utc) + timedelta(hours=1),
            author=self.user, visible=True)
        self.assertEqual(list(Event.objects.get_upcoming()), [event])

    def test_upcomingDate_startYesterdayEndTomorrow_returnEvent(self):
        event = Event.objects.create(name='Event',
            start=datetime.now(timezone.utc) + timedelta(days=-1),
            end=datetime.now(timezone.utc) + timedelta(days=1),
            author=self.user, visible=True)
        self.assertEqual(list(Event.objects.get_upcoming()), [event])

    def test_upcomingDate_startTodayEndToday_returnEvent(self):
        event = Event.objects.create(name='Event',
            start=datetime.now(timezone.utc) + timedelta(minutes=2),
            end=datetime.now(timezone.utc) + timedelta(hours=2),
            author=self.user, visible=True)
        self.assertEqual(list(Event.objects.get_upcoming()), [event])

    def test_upcomingDate_startTodayEndTomorrow_returnEvent(self):
        event = Event.objects.create(name='Event',
            start=datetime.now(timezone.utc) + timedelta(minutes=2),
            end=datetime.now(timezone.utc) + timedelta(days=1),
            author=self.user, visible=True)

        self.assertEqual(list(Event.objects.get_upcoming()), [event])

    def test_upcomingDate_startTomorrowEndTomorrow_returnEvent(self):
        event = Event.objects.create(name='Event',
            start=datetime.now(timezone.utc) + timedelta(days=1),
            end=datetime.now(timezone.utc) + timedelta(days=1),
            author=self.user, visible=True)
        self.assertEqual(list(Event.objects.get_upcoming()), [event])

    def test_upcomingDateUnordered_getDefault_returnCorrectOrder(self):
        event1 = Event.objects.create(name='Event1',
            start=datetime.now(timezone.utc) + timedelta(days=2),
            end=datetime.now(timezone.utc) + timedelta(days=2),
            author=self.user, visible=True)
        event2 = Event.objects.create(name='Event2',
            start=datetime.now(timezone.utc) + timedelta(days=3),
            end=datetime.now(timezone.utc) + timedelta(days=2),
            author=self.user, visible=True)
        event3 = Event.objects.create(name='Event3',
            start=datetime.now(timezone.utc) + timedelta(days=1),
            end=datetime.now(timezone.utc) + timedelta(days=2),
            author=self.user, visible=True)
        self.assertEqual(list(Event.objects.get_upcoming()),
            [event3, event1, event2])

    def test__coordinates_url__no_coordinates(self):
        event = Event.objects.create(name='Event1',
                                     start=datetime.now(timezone.utc),
                                     end=datetime.now(timezone.utc),
                                     author=self.user, visible=True,
                                     )

        self.assertIsNone(event.coordinates_url)

    def test__coordinates_url(self):
        event = Event.objects.create(name='Event1',
                                     start=datetime.now(timezone.utc),
                                     end=datetime.now(timezone.utc),
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

        self.article1 = Article.objects.create(publication_datetime=datetime(2008, 7, 18, 1, 33, 7, tzinfo=timezone.utc),
                                               text='Text 1',
                                               author=self.user,
                                               subject='Article',
                                               category=self.category1,
                                               intro='Intro 1',
                                               )

        self.article2 = Article.objects.create(publication_datetime=datetime(2018, 7, 18, 1, 0, 0, tzinfo=timezone.utc),
                                               text="'''Text 2'''",
                                               author=self.user,
                                               subject='Article',
                                               category=self.category2,
                                               intro='Intro 2',
                                               )

        with freezegun.freeze_time('2024-01-01 12:12'):
            self.comment1 = Comment.objects.create(article=self.article1, text='Text', author=self.user,
                                                   pub_date=datetime.now(timezone.utc))
            self.comment2 = Comment.objects.create(article=self.article1, text='Text2', author=self.user,
                                                   pub_date=datetime.now(timezone.utc))

            self.comment3 = Comment.objects.create(article=self.article2, text='Text3', author=self.user,
                                                   pub_date=datetime.now(timezone.utc))

    def test_position(self):
        self.assertEqual(self.comment1.position, 1)
        self.assertEqual(self.comment2.position, 2)

        # only comment on another article
        self.assertEqual(self.comment3.position, 1)
