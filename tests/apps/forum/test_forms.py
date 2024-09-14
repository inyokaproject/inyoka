"""
    tests.apps.portal.test_views
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test portal forms.

    :copyright: (c) 2012-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from functools import partial

from inyoka.forum.forms import SplitTopicForm
from inyoka.portal.user import User
from inyoka.utils.test import TestCase


class TestSplitTopicForm(TestCase):
    form = SplitTopicForm

    def setUp(self):
        super().setUp()

        self.user = User.objects.create_user('test', 'test@local.test', 'test')
        self.form_create = partial(self.form, user=self.user)

    def test_forum_title_maximum_length(self):
        data = {'new_title': 199*'a'}

        form = self.form_create(data)

        self.assertFalse(form.is_valid())
        self.assertIn('Ensure this value has at most 100 characters (it has 199).', form.errors['new_title'])

    def test_forum_title_valid_length(self):
        data = {'new_title': 99*'a'}

        form = self.form_create(data)

        self.assertNotIn('new_title', form.errors)

