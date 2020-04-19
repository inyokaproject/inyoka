# -*- coding: utf-8 -*-
"""
    tests.wiki.test_forms
    ~~~~~~~~~~~~~~~~~~~~~

    Test some gravatar url creation features.

    :copyright: (c) 2011-2020 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from functools import partial

from mock import patch

from inyoka.portal.user import User
from inyoka.utils.storage import storage
from inyoka.utils.test import TestCase
from inyoka.wiki.models import Page


# disable surge protection for this test case
@patch('inyoka.wiki.forms.NewArticleForm.surge_protection_timeout', None)
class TestNewArticleForm(TestCase):

    def setUp(self):
        super(TestNewArticleForm, self).setUp()

        self.user = User.objects.register_user('user', 'user@example.test', 'user', False)

        from inyoka.wiki.forms import NewArticleForm  # globally the storage table would not exist
        self.form = partial(NewArticleForm, user=self.user)
        self.data = {'name': 'new', 'template': ''}

        storage['wiki_newpage_root'] = 'prefix'

        self._create_page(u'ACL',
                          u'#X-Behave: Access-Control-List\n'
                          u'{{{\n'
                          u'[*]\n'
                          u'user=none\n'
                          u'[prefix/*]\n'
                          u'user=all\n'
                          u'}}}')

    def _create_page(self, name, text, **kwargs):
        return Page.objects.create(name, text, user=self.user, note='comment', **kwargs)

    def _post_form(self):
        form = self.form(data=self.data)
        form.full_clean()

        self.assertEqual(form.cleaned_data['name'],
                         storage['wiki_newpage_root'] + '/' + self.data['name'])

    def test_unprivileged_creates_article(self):
        self._post_form()

    def test_unprivileged_creates_subarticle(self):
        self.data['name'] = 'Howto/new'
        self._post_form()


class TestManageDiscussionForm(TestCase):

    def setUp(self):
        super(TestManageDiscussionForm, self).setUp()

        # globally the storage table would not exist
        from inyoka.wiki.forms import ManageDiscussionForm
        self.form = ManageDiscussionForm

    def test_no_topic(self):
        form = self.form(data={'topic': ''})

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['topic'], None)

    def test_not_existing_topic(self):
        form = self.form(data={'topic': 'not_existing'})

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors,
                         {'topic': [u'This topic does not exist.']})
