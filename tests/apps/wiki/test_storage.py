# -*- coding: utf-8 -*-
from os.path import dirname

from django.conf import settings

from inyoka.portal.user import User
from inyoka.utils.test import InyokaClient, TestCase
from inyoka.wiki.models import Page
from inyoka.wiki.storage import storage

BASE_PATH = dirname(__file__)


class StorageTest(TestCase):

    client_class = InyokaClient

    storage_type = ''

    def setUp(self):
        super(StorageTest, self).setUp()
        self.admin = User.objects.register_user('admin', 'admin', 'admin', False)
        self.client.defaults['HTTP_HOST'] = 'wiki.%s' % settings.BASE_DOMAIN_NAME

        self.client.login(username='admin', password='admin')
        storage.clear_cache()

    def tearDown(self):
        self.client.logout()
        storage.clear_cache()

    def _create_page(self, name, text, **kwargs):
        return Page.objects.create(name, text, user=self.admin,
                                   note='comment', **kwargs)


class TestACLStorage(StorageTest):

    def setUp(self):
        super(TestACLStorage, self).setUp()
        User.objects.register_user('hacker', 'hacker', 'hacker', False)

    def test_single_valid(self):
        self._create_page(u'ACL',
                          u'#X-Behave: Access-Control-List\n'
                          u'{{{\n'
                          u'[*]\n'
                          u'hacker=none\n'
                          u'admin=all\n'
                          u'}}}')

        acl = [(sub, pos, neg) for ptrn, sub, pos, neg in storage.acl]
        self.assertEqual(sorted(acl), [(u'admin', 63, 0), (u'hacker', 0, 63)])

    def test_multiple_valid(self):
        self._create_page(u'ACL',
                          u'#X-Behave: Access-Control-List\n'
                          u'{{{\n'
                          u'[*]\n'
                          u'admin=all\n'
                          u'}}}')

        self._create_page(u'ACL2',
                          u'#X-Behave: Access-Control-List\n'
                          u'{{{\n'
                          u'[*]\n'
                          u'hacker=none\n'
                          u'}}}')

        acl = [(sub, pos, neg) for ptrn, sub, pos, neg in storage.acl]
        self.assertEqual(sorted(acl), [(u'admin', 63, 0), (u'hacker', 0, 63)])

    def test_single_invalid(self):
        self._create_page(u'ACL',
                          u'#X-Behave: Access-Control-List\n'
                          u'{{{\n'
                          u'[*]\n'
                          u'hacker=none\n'
                          u'admin=all\n'
                          u'}}}')

        self._create_page(u'ZZZ/ACL',
                          u'#X-Behave: Access-Control-List\n'
                          u'{{{\n'
                          u'[*]\n'
                          u'admin=none\n'
                          u'hacker=all\n'
                          u'}}}')

        acl = [(sub, pos, neg) for ptrn, sub, pos, neg in storage.acl]
        self.assertEqual(sorted(acl), [(u'admin', 0, 63), (u'admin', 63, 0),
                                       (u'hacker', 0, 63), (u'hacker', 63, 0)])
