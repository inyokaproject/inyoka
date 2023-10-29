"""
    tests.apps.wiki.test_views
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test wiki views.

    :copyright: (c) 2012-2023 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime

from django.conf import settings
from django.test.utils import override_settings
from unittest.mock import patch

from inyoka.portal.user import User
from inyoka.utils.sessions import SurgeProtectionMixin
from inyoka.utils.test import InyokaClient, TestCase
from inyoka.utils.urls import href
from inyoka.wiki.storage import storage
from inyoka.wiki.models import Page


class TestViews(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()
        self.admin = User.objects.register_user('admin', 'admin', 'admin', False)
        self.client.defaults['HTTP_HOST'] = 'wiki.%s' % settings.BASE_DOMAIN_NAME
        self.client.login(username='admin', password='admin')

    @override_settings(PROPAGATE_TEMPLATE_CONTEXT=True)
    @override_settings(WIKI_REVISIONS_PER_PAGE=5)
    def test_log(self):
        p50 = Page.objects.create('Testpage50', 'rev 0', user=self.admin, note='rev 0')
        p100 = Page.objects.create('Testpage100', 'rev 0', user=self.admin, note='rev 0')
        p250 = Page.objects.create('Testpage250', 'rev 0', user=self.admin, note='rev 0')

        for i in range(1, 2):
            p50.edit(text='rev %d' % i, user=self.admin, note='rev %d' % i)
        p50.save()

        for i in range(1, 5):
            p100.edit(text='rev %d' % i, user=self.admin, note='rev %d' % i)
        p100.save()

        for i in range(1, 12):
            p250.edit(text='rev %d' % i, user=self.admin, note='rev %d' % i)
        p250.save()

        req = self.client.get("/Testpage50/a/log", follow=True).content
        self.assertEqual(req.count(b'<tr'), 2)
        req = self.client.get("/Testpage50/a/log/2", follow=True)
        self.assertEqual(req.status_code, 404)

        req = self.client.get("/Testpage100/a/log", follow=True).content
        self.assertEqual(req.count(b'<tr'), 5)
        req = self.client.get("/Testpage100/a/log/2", follow=True)
        self.assertEqual(req.status_code, 404)

        req = self.client.get("/Testpage250/a/log", follow=True).content
        self.assertEqual(req.count(b'<tr'), 5)
        req = self.client.get("/Testpage250/a/log/2", follow=True).content
        self.assertEqual(req.count(b'<tr'), 5)
        req = self.client.get("/Testpage250/a/log/3", follow=True).content
        self.assertEqual(req.count(b'<tr'), 2)
        req = self.client.get("/Testpage250/a/log/4", follow=True)
        self.assertEqual(req.status_code, 404)


class TestDoCreate(TestCase):

    client_class = InyokaClient

    surge_protection_message = SurgeProtectionMixin.surge_protection_message

    def setUp(self):
        super().setUp()
        self.user = User.objects.register_user('user', 'user@example.test', 'user', False)

        self.client.login(username='user', password='user')
        self.client.defaults['HTTP_HOST'] = 'wiki.%s' % settings.BASE_DOMAIN_NAME
        self.url = href('wiki', 'wiki', 'create')

        storage.clear_cache()

    def test_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_simple_create(self):
        self.client.post(self.url, data={'name': 'newpage', 'template': ''})

        self.assertEqual(Page.objects.get().name, 'newpage')

    def test_normalization_create(self):
        self.client.post(self.url, data={'name': 'new page', 'template': ''})

        self.assertEqual(Page.objects.get().name, 'new_page')

    def test_error_with_different_pagename_case(self):
        Page.objects.create(user=self.user, name='abc', remote_addr='', text='test')

        response = self.client.post(self.url, data={'name': 'Abc', 'template': ''})

        self.assertEqual(Page.objects.count(), 1)
        self.assertContains(response, 'The page Abc already exists.')

    def _create_page(self, name):
            return self.client.post(self.url, data={'name': name, 'template': ''}, follow=True)

    @patch('inyoka.portal.models.User.is_team_member', False)
    def test_surge_protection(self):
        response = self._create_page('p1')
        self.assertNotContains(response, self.surge_protection_message)

        response = self._create_page('should_timeout')
        self.assertContains(response, self.surge_protection_message)

    @patch('inyoka.portal.models.User.is_team_member', True)
    def test_surge_protection__not_affects_team_member(self):
        response = self._create_page('p1')
        self.assertNotContains(response, self.surge_protection_message)

        response = self._create_page('no_timeout')
        self.assertNotContains(response, self.surge_protection_message)


class TestDoEdit(TestCase):

    client_class = InyokaClient

    surge_protection_message = SurgeProtectionMixin.surge_protection_message

    def setUp(self):
        super().setUp()
        self.user = User.objects.register_user('user', 'user@example.test', 'user', False)

        self.client.login(username='user', password='user')
        self.client.defaults['HTTP_HOST'] = 'wiki.%s' % settings.BASE_DOMAIN_NAME

        self.page = Page.objects.create(user=self.user, name='abc', remote_addr='', text='test')
        self.url = self.page.get_absolute_url('edit')

    def _edit_page(self, new_content):
        data = {'text': new_content, 'note': new_content, 'edit_time': datetime.utcnow(),
                'revision': self.page.last_rev_id}
        return self.client.post(self.url, data=data, follow=True)

    @patch('inyoka.portal.models.User.is_team_member', False)
    def test_surge_protection(self):
        response = self._edit_page('p1')
        self.assertNotContains(response, self.surge_protection_message)

        response = self._edit_page('should_timeout')
        self.assertContains(response, self.surge_protection_message)

    @patch('inyoka.portal.models.User.is_team_member', True)
    def test_surge_protection__not_affects_team_member(self):
        response = self._edit_page('p1')
        self.assertNotContains(response, self.surge_protection_message)

        response = self._edit_page('no_timeout')
        self.assertNotContains(response, self.surge_protection_message)


class TestDoShow(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()
        self.user = User.objects.register_user('user', 'user@example.test', 'user', False)

        self.page_name = 'test_page'
        page = Page.objects.create(user=self.user, name=self.page_name, remote_addr='', text=self.page_name)
        self.url = page.get_absolute_url('show')

        self.client.login(username='user', password='user')
        self.client.defaults['HTTP_HOST'] = 'wiki.%s' % settings.BASE_DOMAIN_NAME

    def test_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_redirect(self):
        text = f'# X-Redirect: {self.page_name}\nfoobar content'
        redirect = Page.objects.create(user=self.user, name='redirect', remote_addr='', text=text)

        response = self.client.get(redirect.get_absolute_url('show'), follow=True)
        self.assertRedirects(response, self.url)
        self.assertContains(
            response,
            '<a href="http://wiki.ubuntuusers.local:8080/redirect/no_redirect/">redirect</a>',
            html=True
        )

    def test_redirect_loop(self):
        name = 'redirect'
        text = f'# X-Redirect: {name}\nfoobar content'
        redirect = Page.objects.create(user=self.user, name=name, remote_addr='', text=text)

        response = self.client.get(redirect.get_absolute_url('show'), follow=True)
        self.assertRedirects(response, redirect.get_absolute_url('show_no_redirect'))


class TestDoMetaExport(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()
        user = User.objects.register_user('user', 'user@example.test', 'user', False)

        page_name = 'test_page'
        Page.objects.create(user=user, name=page_name, remote_addr='', text=page_name)
        self.url = href('wiki', page_name, 'a', 'export', 'meta')

        self.client.login(username='user', password='user')
        self.client.defaults['HTTP_HOST'] = 'wiki.%s' % settings.BASE_DOMAIN_NAME

    def test_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        # would need a celery task to run, to contain any content
        self.assertEqual(b'', response.content)

    def test_missing_page(self):
        response = self.client.get(href('wiki', 'not_existing', 'a', 'export', 'meta'))
        self.assertEqual(response.status_code, 404)


class TestDoDiff(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()
        self.user = User.objects.register_user('user', 'user@example.test', 'user', False)

        self.page_name = 'test_page'
        self.page = Page.objects.create(user=self.user, name=self.page_name, remote_addr='', text=self.page_name)
        self.page.edit(text='new text', user=self.user)

        self.client.login(username='user', password='user')
        self.client.defaults['HTTP_HOST'] = 'wiki.%s' % settings.BASE_DOMAIN_NAME

    def test_diff__no_param(self):
        url = self.page.get_absolute_url('diff')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_udiff__no_param(self):
        url = self.page.get_absolute_url('udiff')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, b')\n@@ -1 +1 @@\n-test_page\n+new text')

    def test_diff__only_old_revision(self):
        url = self.page.get_absolute_url('diff', revision=Page.objects.get_head(self.page_name, -1))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_udiff__only_old_revision(self):
        url = self.page.get_absolute_url('udiff', revision=Page.objects.get_head(self.page_name, -1))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, b')\n@@ -1 +1 @@\n-test_page\n+new text')

    def test_diff__two_revisions(self):
        self.page.edit(text='new text #2', user=self.user)
        url = self.page.get_absolute_url(
            'diff',
            revision=Page.objects.get_head(self.page_name, -2),
            new_revision=Page.objects.get_head(self.page_name, 0)
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_udiff__two_revisions(self):
        self.page.edit(text='new text #2', user=self.user)
        url = self.page.get_absolute_url(
            'udiff',
            revision=Page.objects.get_head(self.page_name, -2),
            new_revision=Page.objects.get_head(self.page_name, 0)
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, b')\n@@ -1 +1 @@\n-test_page\n+new text #2')

    def test_diff__invalid_new_revision(self):
        url = self.page.get_absolute_url('diff', revision=1, new_revision='1a')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_udiff__invalid_new_revision(self):
        url = self.page.get_absolute_url('udiff', revision=1, new_revision='a')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
