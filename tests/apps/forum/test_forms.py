"""
    tests.apps.portal.test_views
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test portal forms.

    :copyright: (c) 2012-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from functools import partial

from guardian.shortcuts import assign_perm

from inyoka.forum.forms import SplitTopicForm
from inyoka.forum.models import Forum
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

    def _create_forum_objects(self):
        self.user.status = User.STATUS_ACTIVE
        self.user.save()

        category = Forum(name='category')
        category.save()
        forum1 = Forum(name='forum1', parent=category)
        forum1.save()

        assign_perm('forum.view_forum', self.user, category)
        assign_perm('forum.view_forum', self.user, forum1)

        return category, forum1

    def test_forum_validation(self):
        _, forum1 = self._create_forum_objects()

        data = {'new_title': 45 * 'a', 'action': 'new', 'forum': forum1.id,}

        form = self.form_create(data)
        self.assertTrue(form.is_valid())
        self.assertNotIn('forum', form.errors)

    def test_category_validation(self):
        category, _ = self._create_forum_objects()

        data = {'new_title': 45 * 'a', 'action': 'new', 'forum': category.id,}

        form = self.form_create(data)
        self.assertFalse(form.is_valid())
        self.assertIn('forum', form.errors)
