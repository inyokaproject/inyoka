#-*- coding: utf-8 -*-
"""
    tests.apps.wiki.test_views
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test wiki views.

    :copyright: (c) 2012-2015 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.conf import settings
from django.test.utils import override_settings
from mock import patch

from inyoka.portal.user import User
from inyoka.utils.test import InyokaClient, TestCase
from inyoka.wiki.models import Page


class TestViews(TestCase):

    client_class = InyokaClient

    def setUp(self):
        self.admin = User.objects.register_user('admin', 'admin', 'admin', False)
        self.client.defaults['HTTP_HOST'] = 'wiki.%s' % settings.BASE_DOMAIN_NAME
        self.client.login(username='admin', password='admin')

    @override_settings(PROPAGATE_TEMPLATE_CONTEXT=True)
    @patch('inyoka.wiki.actions.REVISIONS_PER_PAGE', 5)
    def test_log(self):
        p50 = Page.objects.create('Testpage50', 'rev 0', user=self.admin, note='rev 0')
        p100 = Page.objects.create('Testpage100', 'rev 0', user=self.admin, note='rev 0')
        p250 = Page.objects.create('Testpage250', 'rev 0', user=self.admin, note='rev 0')

        for i in xrange(1, 2):
            p50.edit(text='rev %d' % i, user=self.admin, note='rev %d' % i)
        p50.save()

        for i in xrange(1, 5):
            p100.edit(text='rev %d' % i, user=self.admin, note='rev %d' % i)
        p100.save()

        for i in xrange(1, 12):
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
