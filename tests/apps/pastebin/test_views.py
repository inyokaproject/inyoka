"""
    tests.apps.pastebin.test_views
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test pastebin views.

    :copyright: (c) 2012-2025 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.conf import settings

from inyoka.pastebin.models import Entry
from inyoka.portal.user import User
from inyoka.utils.test import InyokaClient, TestCase


class TestViews(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()
        self.admin = User.objects.register_user('admin', 'admin', 'admin', False)
        self.admin.is_superuser = True
        self.admin.save()

        self.client.defaults['HTTP_HOST'] = 'paste.%s' % settings.BASE_DOMAIN_NAME
        self.client.login(username='admin', password='admin')

    def _create_example_entry(self):
        e = Entry.objects.create(title="foobar title", lang='html', author=self.admin,
                             code='''<!DOCTYPE html>
<html>
<head><title>Test</title>/head>
<body><p>Test</p></body>
</html>''')

        return e

    def test_add(self):
        data = {
            'lang': 'html',
            'code': '<!DOCTYPE html>',
        }
        response = self.client.post('/add/', data=data, follow=True)
        self.assertEqual(Entry.objects.count(), 1)

        self.assertContains(response, 'Your entry was successfully saved.', count=1)
        self.assertContains(response, '<h1>Untitled</h1>', count=1)

    def test_add__form_displayed(self):
        response = self.client.get('/add/')
        self.assertEqual(response.status_code, 200)

    def test_display(self):
        e = self._create_example_entry()

        response = self.client.get(f'/{e.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<h1>foobar title</h1>", count=1)

    def test_display__not_existing(self):
        response = self.client.get('/555/')
        self.assertEqual(response.status_code, 404)

    def test_delete__not_existing(self):
        response = self.client.get('/delete/555/')
        self.assertEqual(response.status_code, 404)

    def test_delete__form_displayed(self):
        e = self._create_example_entry()

        response = self.client.get(f'/delete/{e.id}/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Do you really want to delete the entry", count=1)

    def test_delete(self):
        e = self._create_example_entry()

        response = self.client.post(f'/delete/{e.id}/', follow=True)
        self.assertContains(response, 'The entry in the pastebin was deleted.', count=1)
        self.assertEqual(Entry.objects.count(), 0)

    def test_delete__cancel(self):
        e = self._create_example_entry()

        response = self.client.post(f'/delete/{e.id}/', data={'cancel': 'C'}, follow=True)
        self.assertContains(response, 'The deletion was canceled', count=1)
        self.assertEqual(Entry.objects.count(), 1)

    def test_browse__no_entries(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No pastes were created yet.", count=1)

    def test_browse__one_entry(self):
        self._create_example_entry()

        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "foobar title", count=1)

    def test_raw__not_existing(self):
        response = self.client.get('/raw/567/')
        self.assertEqual(response.status_code, 404)

    def test_raw(self):
        e = self._create_example_entry()

        response = self.client.get(f'/raw/{e.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<body><p>Test</p></body>", count=1)
