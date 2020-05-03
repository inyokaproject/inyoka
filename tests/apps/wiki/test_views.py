# -*- coding: utf-8 -*-
"""
    tests.apps.wiki.test_views
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test wiki views.

    :copyright: (c) 2012-2020 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime
from unittest import skip

from django.conf import settings
from django.test.utils import override_settings
from mock import patch

from inyoka.portal.user import User
from inyoka.utils.sessions import SurgeProtectionMixin
from inyoka.utils.test import InyokaClient, TestCase
from inyoka.utils.urls import href
from inyoka.wiki.storage import storage
from inyoka.wiki.models import Page


@skip
class TestViews(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super(TestViews, self).setUp()
        self.admin = User.objects.register_user('admin', 'admin', 'admin', False)
        self.client.defaults['HTTP_HOST'] = 'wiki.%s' % settings.BASE_DOMAIN_NAME
        self.client.login(username='admin', password='admin')

    @override_settings(PROPAGATE_TEMPLATE_CONTEXT=True)
    @patch('inyoka.wiki.actions.REVISIONS_PER_PAGE', 5)
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

        req = self.client.get("/Testpage50/a/log").content
        self.assertEqual(req.count('<tr class="odd">') + req.count('<tr class="even">'), 2)
        req = self.client.get("/Testpage50/a/log/2")
        self.assertEqual(req.status_code, 404)

        req = self.client.get("/Testpage100/a/log").content
        self.assertEqual(req.count('<tr class="odd">') + req.count('<tr class="even">'), 5)
        req = self.client.get("/Testpage100/a/log/2")
        self.assertEqual(req.status_code, 404)

        req = self.client.get("/Testpage250/a/log").content
        self.assertEqual(req.count('<tr class="odd">') + req.count('<tr class="even">'), 5)
        req = self.client.get("/Testpage250/a/log/2").content
        self.assertEqual(req.count('<tr class="odd">') + req.count('<tr class="even">'), 5)
        req = self.client.get("/Testpage250/a/log/3").content
        self.assertEqual(req.count('<tr class="odd">') + req.count('<tr class="even">'), 2)
        req = self.client.get("/Testpage250/a/log/4")
        self.assertEqual(req.status_code, 404)


class TestDoCreate(TestCase):

    client_class = InyokaClient

    surge_protection_message = SurgeProtectionMixin.surge_protection_message

    def setUp(self):
        super(TestDoCreate, self).setUp()
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
        super(TestDoEdit, self).setUp()
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
