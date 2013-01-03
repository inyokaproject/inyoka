#-*- coding: utf-8 -*-
"""
    tests.functional.apps.wiki.test_views
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test wiki views.

    :copyright: (c) 2012-2013 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL.
"""
from mock import patch
from random import randint

from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings

from inyoka.wiki.models import Page
from inyoka.portal.user import User
from inyoka.utils.test import InyokaClient


class TestViews(TestCase):

    client_class = InyokaClient

    def setUp(self):
        self.admin = User.objects.register_user('admin', 'admin', 'admin', False)
        self.client.defaults['HTTP_HOST'] = 'wiki.%s' % settings.BASE_DOMAIN_NAME
        self.client.login(username='admin', password='admin')

    @override_settings(PROPAGATE_TEMPLATE_CONTEXT=True)
    def test_log(self):
        p50 = Page.objects.create('Testpage50', 'rev 0', user=self.admin, note='rev 0')
        p100 = Page.objects.create('Testpage100', 'rev 0', user=self.admin, note='rev 0')
        p250 = Page.objects.create('Testpage250', 'rev 0', user=self.admin, note='rev 0')

        for i in xrange(1, 50):
            p50.edit(text='rev %d' % i, user=self.admin, note='rev %d' % i)
        p50.save()

        for i in xrange(1, 100):
            p100.edit(text='rev %d' % i, user=self.admin, note='rev %d' % i)
        p100.save()

        for i in xrange(1, 250):
            p250.edit(text='rev %d' % i, user=self.admin, note='rev %d' % i)
        p250.save()

        req = self.client.get("/Testpage50?action=log").content
        self.assertEqual(req.count('<tr class="odd">') + req.count('<tr class="even">'), 50)
        req = self.client.get("/Testpage50?action=log&page=2")
        self.assertEqual(req.status_code, 404)

        req = self.client.get("/Testpage100?action=log").content
        self.assertEqual(req.count('<tr class="odd">') + req.count('<tr class="even">'), 100)
        req = self.client.get("/Testpage100?action=log&page=2")
        self.assertEqual(req.status_code, 404)

        req = self.client.get("/Testpage250?action=log").content
        self.assertEqual(req.count('<tr class="odd">') + req.count('<tr class="even">'), 100)
        req = self.client.get("/Testpage250?action=log&page=2").content
        self.assertEqual(req.count('<tr class="odd">') + req.count('<tr class="even">'), 100)
        req = self.client.get("/Testpage250?action=log&page=3").content
        self.assertEqual(req.count('<tr class="odd">') + req.count('<tr class="even">'), 50)
        req = self.client.get("/Testpage250?action=log&page=4")
        self.assertEqual(req.status_code, 404)

    def test_show_dynamic_macros(self):
        Page.objects.create('BlaPage', '|[[PageName()]]|', user=self.admin, note='rev0')
        resp = self.client.get('/BlaPage')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('|BlaPage|', resp.content)
