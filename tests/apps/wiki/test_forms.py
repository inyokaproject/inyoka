from functools import partial

from mock import patch

from inyoka.portal.user import User
from inyoka.utils.storage import storage
from inyoka.utils.test import TestCase
from inyoka.wiki.forms import NewArticleForm
from inyoka.wiki.models import Page


# disable surge protection for this test case
@patch('inyoka.wiki.forms.NewArticleForm.surge_protection_timeout', None)
class TestNewArticleForm(TestCase):

    def setUp(self):
        super(TestNewArticleForm, self).setUp()

        self.user = User.objects.register_user('user', 'user@example.test', 'user', False)

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

