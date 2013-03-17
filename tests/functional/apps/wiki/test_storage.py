#-*- coding: utf-8 -*-
from os.path import dirname, join

from django.conf import settings
from django.core.files import File
from django.test import TestCase
from django.test.utils import override_settings

from inyoka.portal.user import User
from inyoka.utils.test import InyokaClient
from inyoka.utils.urls import href
from inyoka.wiki.models import Attachment, Page
from inyoka.wiki.storage import storage
from inyoka.wiki.utils import get_smilies


BASE_PATH = dirname(__file__)


class StorageTest(TestCase):

    client_class = InyokaClient

    storage_type = ''

    def setUp(self):
        self.admin = User.objects.register_user('admin', 'admin', 'admin', False)
        self.client.defaults['HTTP_HOST'] = 'wiki.%s' % settings.BASE_DOMAIN_NAME

        self.client.login(username='admin', password='admin')
        storage.clear_cache(self.storage_type)

    def tearDown(self):
        self.client.logout()
        Page.objects.all().delete()
        Attachment.objects.all().delete()
        storage.clear_cache(self.storage_type)

    def _create_page(self, name, text, **kwargs):
        return Page.objects.create(name, text, user=self.admin,
                                   note='comment', **kwargs)


class TestACLStorage(StorageTest):

    SINGLE_VALID = settings.WIKI_STORAGE_PAGES.copy()
    MULTIPLE_VALID = settings.WIKI_STORAGE_PAGES.copy()
    SINGLE_INVALID = settings.WIKI_STORAGE_PAGES.copy()

    storage_type = 'acl'

    @classmethod
    def setUpClass(cls):
        TestACLStorage.SINGLE_VALID.update({'acl': ('ACL',)})
        TestACLStorage.MULTIPLE_VALID.update({'acl': ('ACL', 'ACL2')})
        TestACLStorage.SINGLE_INVALID.update({'acl': ('ACL',)})

        cls.hacker = User.objects.register_user('hacker', 'hacker', 'hacker', False)

    @override_settings(WIKI_STORAGE_PAGES=SINGLE_VALID)
    def test_single_valid(self):
        self._create_page(u'ACL',
                          u'{{{\n'
                          u'[*]\n'
                          u'hacker=none\n'
                          u'admin=all\n'
                          u'}}}')

        acl = [(sub, pos, neg) for ptrn, sub, pos, neg in storage.acl]
        self.assertEqual(sorted(acl), [(u'admin', 63, 0), (u'hacker', 0, 63)])

    @override_settings(WIKI_STORAGE_PAGES=MULTIPLE_VALID)
    def test_multiple_valid(self):
        self._create_page(u'ACL',
                          u'{{{\n'
                          u'[*]\n'
                          u'admin=all\n'
                          u'}}}')

        self._create_page(u'ACL2',
                          u'{{{\n'
                          u'[*]\n'
                          u'hacker=none\n'
                          u'}}}')

        acl = [(sub, pos, neg) for ptrn, sub, pos, neg in storage.acl]
        self.assertEqual(sorted(acl), [(u'admin', 63, 0), (u'hacker', 0, 63)])

    @override_settings(WIKI_STORAGE_PAGES=SINGLE_INVALID)
    def test_single_invalid(self):
        self._create_page(u'ACL',
                          u'{{{\n'
                          u'[*]\n'
                          u'hacker=none\n'
                          u'admin=all\n'
                          u'}}}')

        self._create_page(u'ZZZ/ACL',
                          u'{{{\n'
                          u'[*]\n'
                          u'admin=none\n'
                          u'hacker=all\n'
                          u'}}}')

        acl = [(sub, pos, neg) for ptrn, sub, pos, neg in storage.acl]
        self.assertEqual(sorted(acl), [(u'admin', 63, 0), (u'hacker', 0, 63)])


class TestInterwikiStorage(StorageTest):

    SINGLE_VALID = settings.WIKI_STORAGE_PAGES.copy()
    MULTIPLE_VALID = settings.WIKI_STORAGE_PAGES.copy()
    SINGLE_INVALID = settings.WIKI_STORAGE_PAGES.copy()

    storage_type = 'interwiki'

    @classmethod
    def setUpClass(cls):
        TestInterwikiStorage.SINGLE_VALID.update({'interwiki': ('IWM',)})
        TestInterwikiStorage.MULTIPLE_VALID.update({'interwiki': ('IWM', 'IWM2')})
        TestInterwikiStorage.SINGLE_INVALID.update({'interwiki': ('IWM',)})

    @override_settings(WIKI_STORAGE_PAGES=SINGLE_VALID)
    def test_single_valid(self):
        self._create_page(u'IWM',
                          u'{{{\n'
                          u'github = https://github.com/\n'
                          u'}}}')
        self.assertEqual(storage.interwiki.get('github'),
                         'https://github.com/')

    @override_settings(WIKI_STORAGE_PAGES=MULTIPLE_VALID)
    def test_multiple_valid(self):
        self._create_page(u'IWM',
                          u'{{{\n'
                          u'github = https://github.com/\n'
                          u'}}}')

        self._create_page(u'IWM2',
                          u'{{{\n'
                          u'google = https://www.google.com/search?q=\n'
                          u'}}}')

        self.assertEqual(storage.interwiki.get('github'),
                         'https://github.com/')
        self.assertEqual(storage.interwiki.get('google'),
                         'https://www.google.com/search?q=')

    @override_settings(WIKI_STORAGE_PAGES=SINGLE_INVALID)
    def test_single_invalid(self):
        self._create_page(u'IWM',
                          u'{{{\n'
                          u'github = https://github.com/\n'
                          u'}}}')

        self._create_page(u'Evil/IWM',
                          u'{{{\n'
                          u'evil = http://example.com/'
                          u'}}}')

        self.assertEqual(storage.interwiki.get('github'),
                         'https://github.com/')
        self.assertEqual(storage.interwiki.get('google'), None)


class TestSmileyStorage(StorageTest):

    SINGLE_VALID = settings.WIKI_STORAGE_PAGES.copy()
    MULTIPLE_VALID = settings.WIKI_STORAGE_PAGES.copy()
    SINGLE_INVALID = settings.WIKI_STORAGE_PAGES.copy()

    FILE_ANGEL = 'angel.png'
    FILE_EVIL = 'evil.png'
    FILE_HAPPY = 'happy.png'

    storage_type = 'smilies'

    @classmethod
    def setUpClass(cls):
        TestSmileyStorage.SINGLE_VALID.update({'smilies': ('SmiliesSV',)})
        TestSmileyStorage.MULTIPLE_VALID.update({'smilies': ('SmiliesMV', 'MoreMV')})
        TestSmileyStorage.SINGLE_INVALID.update({'smilies': ('SmiliesSI',)})

    @override_settings(WIKI_STORAGE_PAGES=SINGLE_VALID)
    def test_single_valid(self):
        f = open(join(BASE_PATH, self.FILE_HAPPY), 'rb')
        att = self._create_page(u'SmiliesSV/happy_sv.png', '',
                                attachment_filename=u'happy_sv.png',
                                attachment=File(f))

        self._create_page(u'SmiliesSV',
                          u'{{{\n'
                          u':-) = SmiliesSV/happy_sv.png\n'
                          u'}}}')

        expect = [(u':-)', href('media', att.last_rev.attachment.file.name))]

        self.assertEqual(get_smilies(), expect)

    @override_settings(WIKI_STORAGE_PAGES=MULTIPLE_VALID)
    def test_multiple_valid(self):
        f1 = open(join(BASE_PATH, self.FILE_HAPPY), 'rb')
        att1 = self._create_page(u'SmiliesMV/happy_mv.png', '',
                                 attachment_filename=u'happy_mv.png',
                                 attachment=File(f1))

        f2 = open(join(BASE_PATH, self.FILE_ANGEL), 'rb')
        att2 = self._create_page(u'MoreMV/angel_mv.png', '',
                                 attachment_filename=u'angel_mv.png',
                                 attachment=File(f2))

        self._create_page(u'SmiliesMV',
                          u'{{{\n'
                          u':-) = SmiliesMV/happy_mv.png\n'
                          u'}}}')

        self._create_page(u'MoreMV',
                          u'{{{\n'
                          u'O:-) = MoreMV/angel_mv.png\n'
                          u'}}}')

        expect = [(u'O:-)', href('media', att2.last_rev.attachment.file.name)),
                  (u':-)', href('media', att1.last_rev.attachment.file.name))]

        self.assertEqual(get_smilies(), expect)

    @override_settings(WIKI_STORAGE_PAGES=SINGLE_INVALID)
    def test_single_invalid(self):
        f1 = open(join(BASE_PATH, self.FILE_HAPPY), 'rb')
        att1 = self._create_page(u'SmiliesSI/happy_si.png', '',
                                 attachment_filename=u'happy_si.png',
                                 attachment=File(f1))

        f2 = open(join(BASE_PATH, self.FILE_HAPPY), 'rb')
        self._create_page(u'EvilSI/evil_si.png', '',
                          attachment_filename=u'evil_si.png',
                          attachment=File(f2))

        self._create_page(u'SmiliesSI',
                          u'{{{\n'
                          u':-) = SmiliesSI/happy_si.png\n'
                          u'}}}')

        self._create_page(u'EvliSI',
                          u'{{{\n'
                          u']:-( = EvliSI/evil_si.png\n'
                          u'}}}')

        expect = [(u':-)', href('media', att1.last_rev.attachment.file.name))]
        self.assertEqual(get_smilies(), expect)
