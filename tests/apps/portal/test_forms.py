# -*- coding: utf-8 -*-
"""
    tests.apps.portal.test_views
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test portal views.

    :copyright: (c) 2012-2017 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from functools import partial

from inyoka.portal.models import StaticPage
from inyoka.utils.test import TestCase

from inyoka.portal.forms import EditStaticPageForm


class TestEditStaticPageForm(TestCase):
    form = EditStaticPageForm

    form_edit = partial(form, new=False)
    form_create = partial(form, new=True)

    def test_create_with_already_existing_key(self):
        StaticPage.objects.create(key='foo', title='foo',
                                  content='Nobody likes foo?')

        title = 'FOO'
        data = {'key': title, 'title': title,
                'content': 'Nobody likes foo?'}
        form = self.form_create(data)

        self.assertFalse(form.is_valid())
        self.assertIn('Another page with this name already exists. Please '
                      'edit this page.', form.errors['__all__'])

    def test_create_valid_data(self):
        title = 'foo'
        data = {'key': title, 'title': title, 'content': 'Nobody likes foo?'}
        form = self.form_create(data)

        self.assertTrue(form.is_valid())

    def test_create_without_user_defined_key(self):
        title = 'foo'
        data = {'key': '', 'title': title, 'content': 'Nobody likes foo?'}
        form = self.form_create(data)

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['key'], title)

    def test_create_key_with_different_case_to_existing_page(self):
        StaticPage.objects.create(key='foo', title='foo',
                                  content='Nobody likes foo?')

        title = 'FOO'
        data = {'key': title, 'title': title, 'content': 'Nobody likes foo?'}
        form = self.form_create(data)

        self.assertFalse(form.is_valid())
        self.assertIn('Another page with this name already exists. Please '
                      'edit this page.', form.errors['__all__'])

    def test_create_title_with_different_case_to_existing_page(self):
        StaticPage.objects.create(key='foo', title='foo',
                                  content='Nobody likes foo?')

        title = 'FOO'
        data = {'key': '', 'title': title, 'content': 'Nobody likes foo?'}
        form = self.form_create(data)

        self.assertFalse(form.is_valid())
        self.assertIn('Another page with this name already exists. Please '
                      'edit this page.', form.errors['__all__'])

    def test_edit_only_content(self):
        title = 'foo'
        page = StaticPage.objects.create(key=title, title=title,
                                         content='Nobody likes foo?')
        form = self.form_edit({'key': page.title, 'title': page.title, 'content': 'edited'},
                              instance=page)

        self.assertTrue(form.is_valid())

    def test_edit_only_title(self):
        title = 'foo'
        page = StaticPage.objects.create(key=title, title=title,
                                         content='Nobody likes foo?')
        form = self.form_edit({'key': page.title, 'title': 'edited', 'content': page.content},
                              instance=page)

        self.assertTrue(form.is_valid())

    def test_edit_key_changed(self):
        title = 'foo'
        page = StaticPage.objects.create(key=title, title=title,
                                         content='Nobody likes foo?')
        form = self.form_edit({'key': '123', 'title': page.title, 'content': page.content},
                              instance=page)

        self.assertFalse(form.is_valid())
        self.assertIn('It is not allowed to change this key.', form.errors['key'])

    def test_create_empty_title_and_key(self):
        form = self.form_create({'key': '', 'title': '', 'content': 'foo'})
        self.assertFalse(form.is_valid())
        self.assertIn('This field is required.', form.errors['title'])

    def test_space_as_title(self):
        form = self.form_create({'key': '', 'title': ' ', 'content': 'foo'})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['key'], '-')
