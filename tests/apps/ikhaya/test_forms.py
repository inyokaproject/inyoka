"""
    tests.apps.ikhaya.test_views
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test ikhaya forms.

    :copyright: (c) 2012-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from inyoka.ikhaya.forms import EditCommentForm
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
