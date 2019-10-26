# -*- coding: utf-8 -*-
from os.path import dirname, join

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
        self._create_page('ACL',
                          '#X-Behave: Access-Control-List\n'
                          '{{{\n'
                          '[*]\n'
                          'hacker=none\n'
                          'admin=all\n'
                          '}}}')

        acl = [(sub, pos, neg) for ptrn, sub, pos, neg in storage.acl]
        self.assertEqual(sorted(acl), [('admin', 63, 0), ('hacker', 0, 63)])

    def test_multiple_valid(self):
        self._create_page('ACL',
                          '#X-Behave: Access-Control-List\n'
                          '{{{\n'
                          '[*]\n'
                          'admin=all\n'
                          '}}}')

        self._create_page('ACL2',
                          '#X-Behave: Access-Control-List\n'
                          '{{{\n'
                          '[*]\n'
                          'hacker=none\n'
                          '}}}')

        acl = [(sub, pos, neg) for ptrn, sub, pos, neg in storage.acl]
        self.assertEqual(sorted(acl), [('admin', 63, 0), ('hacker', 0, 63)])

    def test_single_invalid(self):
        self._create_page('ACL',
                          '#X-Behave: Access-Control-List\n'
                          '{{{\n'
                          '[*]\n'
                          'hacker=none\n'
                          'admin=all\n'
                          '}}}')

        self._create_page('ZZZ/ACL',
                          '#X-Behave: Access-Control-List\n'
                          '{{{\n'
                          '[*]\n'
                          'admin=none\n'
                          'hacker=all\n'
                          '}}}')

        acl = [(sub, pos, neg) for ptrn, sub, pos, neg in storage.acl]
        self.assertEqual(sorted(acl), [('admin', 0, 63), ('admin', 63, 0),
                                       ('hacker', 0, 63), ('hacker', 63, 0)])


class TestInterwikiStorage(StorageTest):

    def test_single_valid(self):
        self._create_page('IWM',
                          '#X-Behave: Interwiki-Map\n'
                          '{{{\n'
                          'github = https://github.com/\n'
                          '}}}')
        self.assertEqual(storage.interwiki.get('github'),
                         'https://github.com/')

    def test_multiple_valid(self):
        self._create_page('IWM',
                          '#X-Behave: Interwiki-Map\n'
                          '{{{\n'
                          'github = https://github.com/\n'
                          '}}}')

        self._create_page('IWM2',
                          '#X-Behave: Interwiki-Map\n'
                          '{{{\n'
                          'google = https://www.google.com/search?q=\n'
                          '}}}')

        self.assertEqual(storage.interwiki.get('github'),
                         'https://github.com/')
        self.assertEqual(storage.interwiki.get('google'),
                         'https://www.google.com/search?q=')

    def test_single_invalid(self):
        self._create_page('IWM',
                          '#X-Behave: Interwiki-Map\n'
                          '{{{\n'
                          'github = https://github.com/\n'
                          '}}}')

        self._create_page('IWM/Evil',
                          '#X-Behave: Interwiki-Map\n'
                          '{{{\n'
                          'github = http://evil.com/'
                          '}}}')

        self.assertEqual(storage.interwiki.get('github'),
                         'http://evil.com/')
