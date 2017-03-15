# -*- coding: utf-8 -*-
from os.path import dirname, join

from django.conf import settings
from django.core.files import File

from inyoka.portal.user import User
from inyoka.utils.test import InyokaClient, TestCase
from inyoka.utils.urls import href
from inyoka.wiki.models import Page
from inyoka.wiki.storage import storage
from inyoka.wiki.utils import get_smiley_map

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


class TestSmileyStorage(StorageTest):

    FILE_ANGEL = 'angel.png'
    FILE_EVIL = 'evil.png'
    FILE_HAPPY = 'happy.png'

    def test_single_valid(self):
        f = open(join(BASE_PATH, self.FILE_HAPPY), 'rb')
        att = self._create_page(u'SmiliesSV/happy_sv.png', '',
                                attachment_filename=u'happy_sv.png',
                                attachment=File(f))

        self._create_page(u'SmiliesSV',
                          u'#X-Behave: Smiley-Map\n'
                          u'{{{\n'
                          u':-) = SmiliesSV/happy_sv.png\n'
                          u'}}}')

        expect = [(u':-)', href('media', att.last_rev.attachment.file.name))]

        self.assertEqual(get_smiley_map(), expect)

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
                          u'#X-Behave: Smiley-Map\n'
                          u'{{{\n'
                          u':-) = SmiliesMV/happy_mv.png\n'
                          u'}}}')

        self._create_page(u'MoreMV',
                          u'#X-Behave: Smiley-Map\n'
                          u'{{{\n'
                          u'O:-) = MoreMV/angel_mv.png\n'
                          u'}}}')

        expect = [(u'O:-)', href('media', att2.last_rev.attachment.file.name)),
                  (u':-)', href('media', att1.last_rev.attachment.file.name))]

        self.assertEqual(get_smiley_map(), expect)

    def test_single_invalid(self):
        f1 = open(join(BASE_PATH, self.FILE_HAPPY), 'rb')
        att1 = self._create_page(u'SmiliesSI/happy_si.png', '',
                                 attachment_filename=u'happy_si.png',
                                 attachment=File(f1))

        f2 = open(join(BASE_PATH, self.FILE_HAPPY), 'rb')
        att2 = self._create_page(u'SmiliesSI/Evli/evil_si.png', '',
                                 attachment_filename=u'evil_si.png',
                                 attachment=File(f2))

        self._create_page(u'SmiliesSI',
                          u'#X-Behave: Smiley-Map\n'
                          u'{{{\n'
                          u':-) = SmiliesSI/happy_si.png\n'
                          u'}}}')

        self._create_page(u'SmiliesSI/Evli',
                          u'#X-Behave: Smiley-Map\n'
                          u'{{{\n'
                          u':-) = SmiliesSI/Evli/evil_si.png\n'
                          u'}}}')

        expect = [(u':-)', href('media', att2.last_rev.attachment.file.name)),
                  (u':-)', href('media', att1.last_rev.attachment.file.name))]
        self.assertEqual(get_smiley_map(), expect)
