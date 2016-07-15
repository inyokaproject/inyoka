# -*- coding: utf-8 -*-
"""
    tests.utils.test_views
    ~~~~~~~~~~~~~~~~~~~~~~

    Test view mixins.

    :copyright: (c) 2012-2016 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.core.exceptions import ImproperlyConfigured
from django.test import RequestFactory
from inyoka.utils.test import TestCase
from inyoka.utils.views import FormPreviewMixin
from mock import call, Mock, patch


# Some Dummy code
# ---------------
class DummyForm(object):
    """A dummy form to test the `post()` method."""
    valid = True

    def __init__(self, valid=True):
        self.valid = valid

    def is_valid(self):
        return self.valid


class DummyMixin(object):
    """A dummy mixin to provide `get_context_data()` so the `super()` call works."""
    def get_context_data(self):
        return {}


class DummyView(FormPreviewMixin, DummyMixin):
    """Just a dummy to use the mixins in."""


# Actual tests
# ------------
class TestFormPreviewMixin(TestCase):
    """Unit Tests for the FormPreviewMixin."""

    def setUp(self):
        self.view = DummyView()

    @patch('inyoka.utils.views.FormPreviewMixin.render_previews')
    def test_get_context_data_with_preview(self, mock_render_previews):
        """Test that `get_context_data()` adds the `previews` key to the context dict."""
        mock_render_previews.return_value = {}
        self.view.request = RequestFactory().post('/', data={'preview': 'Preview'})
        expected_value = {'previews': {}}

        actual_value = self.view.get_context_data()

        self.assertEqual(expected_value, actual_value)

    @patch('inyoka.utils.views.FormPreviewMixin.render_previews')
    def test_get_context_data_with_submit(self, mock_render_previews):
        """Test that `get_context_data()` does not add the `previews` key, when preview was not pressed."""
        self.view.request = RequestFactory().post('/', data={'submit': 'Submit'})
        expected_value = {}

        actual_value = self.view.get_context_data()

        self.assertEqual(expected_value, actual_value)

    @patch('inyoka.utils.views.FormPreviewMixin.get_preview_fields')
    def test_render_previews(self, mock_get_preview_fields):
        """Test that `render_previews()` returns a dict with the previews."""
        mock_get_preview_fields.return_value = ['testfield']
        expected_value = {'testfield': 'sometext'}
        self.view.preview_method = Mock(return_value='sometext')
        self.view.request = RequestFactory().post('/', data=expected_value)

        actual_value = self.view.render_previews()

        self.assertEqual(expected_value, actual_value)
        self.view.preview_method.assert_called_once_with('sometext')

    @patch('inyoka.utils.views.FormPreviewMixin.get_preview_fields')
    def test_render_previews_multiple_fields(self, mock_get_preview_fields):
        """Test that `render_previews()` returns a dict with the previews."""
        mock_get_preview_fields.return_value = ['testfield1', 'testfield2']
        expected_value = {'testfield1': 'sometext', 'testfield2': 'sometext'}
        self.view.preview_method = Mock(return_value='sometext')
        self.view.request = RequestFactory().post('/', data=expected_value)

        actual_value = self.view.render_previews()

        self.assertEqual(expected_value, actual_value)
        self.view.preview_method.assert_has_calls([call('sometext'), call('sometext')])

    def test_get_preview_fields(self):
        """Test that `get_preview_fields()` returns the list of form fields that should be rendered."""
        expected_value = ['testfield1', 'testfield2']
        self.view.preview_fields = expected_value

        actual_value = self.view.get_preview_fields()

        self.assertEqual(expected_value, actual_value)

    def test_get_preview_fields_improperly_configured(self):
        """Test that `get_preview_fields()` raises ImproperlyConfigured, when self.preview_fields is missing."""
        with self.assertRaises(ImproperlyConfigured):
            self.view.get_preview_fields()

    def test_post_with_preview_pressed(self):
        """Test that `post()` will not submit when "preview" button was pressed."""
        request = RequestFactory().post('/', data={'preview': 'Preview'})
        self.view.get_form = Mock(return_value=DummyForm(valid=True))
        self.view.form_valid = Mock(return_value='valid')
        self.view.form_invalid = Mock(return_value='invalid')
        expected_value = 'invalid'

        actual_value = self.view.post(request)

        self.assertEqual(expected_value, actual_value)

    def test_post_with_valid_form(self):
        """Test that `post()` will call `form_valid()` when submit button was pressed."""
        request = RequestFactory().post('/', data={'submit': 'Submit'})
        self.view.get_form = Mock(return_value=DummyForm(valid=True))
        self.view.form_valid = Mock(return_value='valid')
        self.view.form_invalid = Mock(return_value='invalid')
        expected_value = 'valid'

        actual_value = self.view.post(request)

        self.assertEqual(expected_value, actual_value)

    def test_post_with_invalid_form(self):
        """Test that `post()` will call `form_invalid()` when submitted form was not valid."""
        request = RequestFactory().post('/', data={'submit': 'Submit'})
        self.view.get_form = Mock(return_value=DummyForm(valid=False))
        self.view.form_valid = Mock(return_value='valid')
        self.view.form_invalid = Mock(return_value='invalid')
        expected_value = 'invalid'

        actual_value = self.view.post(request)

        self.assertEqual(expected_value, actual_value)
