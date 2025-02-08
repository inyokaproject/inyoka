"""
    tests.apps.ikhaya.test_forms
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test ikhaya forms.

    :copyright: (c) 2012-2025 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime, timedelta, timezone

from freezegun import freeze_time

from inyoka.ikhaya.forms import (
    EditArticleForm,
    EditCommentForm,
    EditPublicArticleForm,
    NewEventForm,
)
from inyoka.ikhaya.models import Article, Category
from inyoka.portal.user import User
from inyoka.utils.test import TestCase


class TestEditCommentForm(TestCase):
    form = EditCommentForm

    def test_text__whitespace_not_stripped(self):
        text = ' * a \n * b\n'
        data = {'text': text}

        form = self.form(data)

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['text'], text)

    def test_text__empty_text_rejected(self):
        text = ' \n \t'
        data = {'text': text}

        form = self.form(data)

        self.assertFalse(form.is_valid())
        self.assertIn(
            'Text must not be empty',
            form.errors['text'],
        )


class TestEditArticleForm(TestCase):

    form_class = EditArticleForm

    def test_clean_slug__valid(self):
        self.user = User.objects.register_user('admin', 'admin', 'admin', False)
        self.category1 = Category.objects.create(name='Test Category')
        article = Article.objects.create(
            publication_datetime=datetime(2008, 7, 18, 1, 33, 7, tzinfo=timezone.utc),
            text='Text 1',
            author=self.user,
            subject='Article',
            category=self.category1,
            intro='Intro 1',
        )

        form = self.form_class(data={'slug': 'another-slug',
                                     'publication_datetime_0': '2008-07-18',
                                     'publication_datetime_1': '03:33:07'})
        self.assertFalse(form.is_valid()) # fields are missing

        # check that passed datetime is valid
        self.assertNotIn('publication_datetime', form.errors.keys())
        self.assertEqual(form.cleaned_data['publication_datetime'], article.publication_datetime)

        self.assertEqual('another-slug', form.clean_slug())

    def test_clean_slug__valid__with_instance_passed(self):
        self.user = User.objects.register_user('admin', 'admin', 'admin', False)
        self.category1 = Category.objects.create(name='Test Category')
        article = Article.objects.create(
            publication_datetime=datetime(2008, 7, 18, 1, 33, 7, tzinfo=timezone.utc),
            text='Text 1',
            author=self.user,
            subject='Article',
            category=self.category1,
            intro='Intro 1',
        )

        form = self.form_class(data={'slug': article.slug,
                                     'publication_datetime_0': '2008-07-18',
                                     'publication_datetime_1': '03:33:07'},
                               instance=article)
        self.assertFalse(form.is_valid()) # fields are missing

        # check that passed datetime is valid
        self.assertNotIn('publication_datetime', form.errors.keys())
        self.assertEqual(form.cleaned_data['publication_datetime'], article.publication_datetime)

        self.assertEqual(article.slug, form.clean_slug())
        self.assertNotIn('slug', form.errors.keys())

    def test_clean_slug__collision__publication_datetime_equal(self):
        self.user = User.objects.register_user('admin', 'admin', 'admin', False)
        self.category1 = Category.objects.create(name='Test Category')
        article = Article.objects.create(
            publication_datetime=datetime(2008, 7, 18, 1, 33, 7, tzinfo=timezone.utc),
            text='Text 1',
            author=self.user,
            subject='Article',
            category=self.category1,
            intro='Intro 1',
        )

        form = self.form_class(data={'slug': article.slug,
                                     'publication_datetime_0': '2008-07-18',
                                     'publication_datetime_1': '03:33:07'})
        self.assertFalse(form.is_valid()) # fields are missing

        # check that passed datetime is valid
        self.assertNotIn('publication_datetime', form.errors.keys())
        self.assertEqual(form.cleaned_data['publication_datetime'], article.publication_datetime)

        self.assertEqual(['There already exists an article with this slug!'], form.errors['slug'])

    def test_clean_slug__collision__different_minutes(self):
        self.user = User.objects.register_user('admin', 'admin', 'admin', False)
        self.category1 = Category.objects.create(name='Test Category')
        article = Article.objects.create(
            publication_datetime=datetime(2008, 7, 18, 1, 33, 7, tzinfo=timezone.utc),
            text='Text 1',
            author=self.user,
            subject='Article',
            category=self.category1,
            intro='Intro 1',
        )

        form = self.form_class(data={'slug': article.slug,
                                     'publication_datetime_0': '2008-07-18',
                                     'publication_datetime_1': '03:10:00'})
        self.assertFalse(form.is_valid()) # fields are missing

        # check that passed datetime is valid
        self.assertNotIn('publication_datetime', form.errors.keys())

        self.assertEqual(['There already exists an article with this slug!'], form.errors['slug'])

    def test_clean_slug__different_dates_in_UTC(self):
        self.user = User.objects.register_user('admin', 'admin', 'admin', False)
        self.category1 = Category.objects.create(name='Test Category')
        local_timezone = timezone(timedelta(seconds=7200))
        article = Article.objects.create(
            publication_datetime=datetime(2010, 7, 18, 1, 33, 7,
                                             tzinfo=local_timezone),
            text='Text 1',
            author=self.user,
            subject='Article',
            category=self.category1,
            intro='Intro 1',
        )

        form = self.form_class(data={'slug': article.slug,
                                     'publication_datetime_0': '2010-07-18',
                                     'publication_datetime_1': '23:33:00'})
        self.assertFalse(form.is_valid()) # fields are missing

        # check that passed datetime is valid
        self.assertNotIn('publication_datetime', form.errors.keys())

        self.assertEqual(article.slug, form.clean_slug())


    def test_initial_value_updated__published_but_not_updated_article(self):
        self.user = User.objects.register_user('admin', 'admin', 'admin', False)
        self.category1 = Category.objects.create(name='Test Category')
        article = Article.objects.create(
            publication_datetime=datetime(2008, 7, 18, 1, 33, 7, tzinfo=timezone.utc),
            text='Text 1',
            author=self.user,
            subject='Article',
            category=self.category1,
            intro='Intro 1',
            public=True,
        )
        self.assertIsNone(article.updated)

        with freeze_time('2024-04-01 11:23:55Z'):
            form = self.form_class(instance=article)
            self.assertIn('name="updated_0" value="2024-04-01"', form.as_div())

    def test_value_updated__published_and_already_updated_article(self):
        self.user = User.objects.register_user('admin', 'admin', 'admin', False)
        self.category1 = Category.objects.create(name='Test Category')
        article = Article.objects.create(
            publication_datetime=datetime(2008, 7, 18, 1, 33, 7, tzinfo=timezone.utc),
            updated=datetime(2010, 10, 18, 10, tzinfo=timezone.utc),
            text='Text 1',
            author=self.user,
            subject='Article',
            category=self.category1,
            intro='Intro 1',
            public=True,
        )

        with freeze_time('2024-04-01 11:23:55Z'):
            form = self.form_class(instance=article)
            # should be still in 2010 (the last time the article was updated)
            self.assertIn('name="updated_0" value="2010-10-18"', form.as_div())

    def test_updated_field_removed_if_no_instance(self):
        form = self.form_class()
        self.assertNotIn('updated', form.fields.keys())

    def test_public_article_form__missing_fields(self):
        self.assertNotIn('slug', EditPublicArticleForm().fields.keys())
        self.assertNotIn('publication_datetime', EditPublicArticleForm().fields.keys())


class TestNewEventForm(TestCase):

    form_class = NewEventForm

    def test_valid_form(self):
        data = {
            'name': 'foo',
            'start_0': '2022-12-02',
            'start_1': '11:11:11',
            'end_0': '2022-12-03',
            'end_1': '10:10:0',
        }

        form = self.form_class(data=data)
        self.assertTrue(form.is_valid())

    def test_missing_location_long(self):
        data = {
            'name': 'foo',
            'start_0': '2022-12-02',
            'start_1': '11:11:11',
            'end_0': '2022-12-03',
            'end_1': '10:10:0',
            'location_lat': 2,
        }

        form = self.form_class(data=data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['location_long'],
                         ['You must specify a location longitude.'])

    def test_missing_location_lat(self):
        data = {
            'name': 'foo',
            'start_0': '2022-12-02',
            'start_1': '11:11:11',
            'end_0': '2022-12-03',
            'end_1': '10:10:0',
            'location_long': 2,
        }

        form = self.form_class(data=data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['location_lat'],
                         ['You must specify a location latitude.'])
