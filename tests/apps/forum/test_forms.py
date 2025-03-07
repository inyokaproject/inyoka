"""
    tests.apps.portal.test_views
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test portal forms.

    :copyright: (c) 2012-2025 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from functools import partial

from guardian.shortcuts import assign_perm

from inyoka.forum.forms import MoveTopicForm, SplitTopicForm
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
        data = {'new_title': 199 * 'a'}

        form = self.form_create(data)

        self.assertFalse(form.is_valid())
        self.assertIn(
            'Ensure this value has at most 100 characters (it has 199).',
            form.errors['new_title'],
        )

    def test_forum_title_valid_length(self):
        data = {'new_title': 99 * 'a'}

        form = self.form_create(data)

        self.assertNotIn('new_title', form.errors)

    def _create_forum_objects(self):
        self.user.status = User.STATUS_ACTIVE
        self.user.save()

        category = Forum(name='category')
        category.save()
        forum1 = Forum(name='forum1', parent=category)
        forum1.save()
        forum2 = Forum(name='forum2', parent=category)
        forum2.save()

        assign_perm('forum.view_forum', self.user, category)
        assign_perm('forum.view_forum', self.user, forum1)
        assign_perm('forum.view_forum', self.user, forum2)

        return category, forum1, forum2

    def test_forum_validation(self):
        _, forum1, _ = self._create_forum_objects()

        data = {
            'new_title': 45 * 'a',
            'action': 'new',
            'forum': forum1.id,
        }

        form = self.form_create(data)
        self.assertTrue(form.is_valid())
        self.assertNotIn('forum', form.errors)

    def test_category_validation(self):
        category, _, _ = self._create_forum_objects()

        data = {
            'new_title': 45 * 'a',
            'action': 'new',
            'forum': category.id,
        }

        form = self.form_create(data)
        self.assertFalse(form.is_valid())
        self.assertIn('forum', form.errors)

    def test_return_value_clean_forum(self):
        _, _, forum2 = self._create_forum_objects()

        data = {'new_title': 45 * 'a', 'action': 'new', 'forum': forum2.id}

        form = self.form_create(data)
        self.assertTrue(form.is_valid())
        form.clean()
        self.assertEqual(form.cleaned_data['forum'], forum2)


class TestMoveTopicForm(TestCase):
    form = MoveTopicForm

    def setUp(self):
        super().setUp()

        self.user = User.objects.create_user('test', 'test@local.test', 'test')
        self.user.status = User.STATUS_ACTIVE
        self.user.save()

        self.category = Forum(name='category')
        self.category.save()
        self.forum1 = Forum(name='forum1', parent=self.category)
        self.forum1.save()

        assign_perm('forum.view_forum', self.user, self.category)
        assign_perm('forum.view_forum', self.user, self.forum1)

        self.form_create = partial(self.form, user=self.user, current_forum=self.forum1)

    def test_move_to_same_forum__raise_error(self):
        data = {'forum': self.forum1.id}

        form = self.form_create(data)
        self.assertFalse(form.is_valid())
        self.assertIn('The topic is already in this forum', form.errors['forum'])

    def test_return_value_clean_forum(self):
        forum2 = Forum(name='forum1', parent=self.category)
        forum2.save()
        assign_perm('forum.view_forum', self.user, forum2)

        data = {'forum': forum2.id}

        form = self.form_create(data)
        self.assertTrue(form.is_valid())
        form.clean()
        self.assertEqual(form.cleaned_data['forum'], forum2)
