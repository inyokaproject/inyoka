# -*- coding: utf-8 -*-
"""
    test_page_rename
    ~~~~~~~~~~~~~~~~

    Test the wiki page rename.

    :copyright: (c) 2012-2020 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.core.files import File
from os.path import join, dirname

from django.test import RequestFactory

from inyoka.portal.user import User
from inyoka.utils.test import TestCase
from inyoka.wiki.models import Page

BASE_PATH = dirname(__file__)


class PageRename(TestCase):

    FILE_ANGEL = 'angel.png'
    FILE_EVIL = 'evil.png'
    FILE_HAPPY = 'happy.png'

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user('test_user', 'test2@inyoka.local')

    def test_rename_page(self):
        page = Page.objects.create(name='test', text='Testfoo', user=self.user,
                                   attachment=None, attachment_filename=None)

        request = self.factory.get('/')
        request.user = self.user

        new_name = 'new_test'
        from inyoka.wiki.actions import _rename  # local import, as __getitem__ of storage uses ORM
        _rename(request, page, new_name)

        page.refresh_from_db()
        self.assertEqual(page.name, new_name)

    def test_rename_attachment(self):
        with open(join(BASE_PATH, self.FILE_HAPPY), 'rb') as f:
            page = Page.objects.create(name='test',
                                       text='',
                                       user=self.user,
                                       attachment=File(f),
                                       attachment_filename=f.name)

        self.assertEqual(len(Page.objects.get_attachment_list()), 1)

        request = self.factory.get('/')
        request.user = self.user

        new_name = 'new_test'
        from inyoka.wiki.actions import _rename  # local import, as __getitem__ of storage uses ORM
        _rename(request, page, new_name)

        page.refresh_from_db()
        self.assertEqual(page.name, new_name)
        self.assertEqual(len(Page.objects.get_attachment_list()), 1)

    def test_rename_page_with_three_attachments(self):
        page = Page.objects.create(name='test', text='Testfoo', user=self.user)

        # create three attachments for `page`
        # they only need to be children („have page.name as prefix“) for `page`
        with open(join(BASE_PATH, self.FILE_HAPPY), 'rb') as happy:
            attachment_happy = Page.objects.create(name='/'.join((page.name, 'attachment_happy')),
                                                   text='',
                                                   user=self.user,
                                                   attachment=File(happy),
                                                   attachment_filename=happy.name)

        with open(join(BASE_PATH, self.FILE_ANGEL), 'rb') as angel:
            attachment_angel = Page.objects.create(name='/'.join((page.name, 'attachment_angel')),
                                                   text='',
                                                   user=self.user,
                                                   attachment=File(angel),
                                                   attachment_filename=angel.name)

        with open(join(BASE_PATH, self.FILE_EVIL), 'rb') as evil:
            attachment_evil = Page.objects.create(name='/'.join((page.name, 'attachment_evil')),
                                                  text='',
                                                  user=self.user,
                                                  attachment=File(evil),
                                                  attachment_filename=evil.name)

        self.assertEqual(len(Page.objects.get_attachment_list(page.name)), 3)

        request = self.factory.get('/')
        request.user = self.user

        new_name = 'new_test'
        from inyoka.wiki.actions import _rename  # local import, as __getitem__ of storage uses ORM
        _rename(request, page, new_name)

        page.refresh_from_db()
        self.assertEqual(page.name, new_name)

        attachment_happy.refresh_from_db()
        self.assertTrue(attachment_happy.name.startswith(page.name))

        attachment_angel.refresh_from_db()
        self.assertTrue(attachment_angel.name.startswith(page.name))

        attachment_evil.refresh_from_db()
        self.assertTrue(attachment_evil.name.startswith(page.name))

    def test_rename_page_with_hundred_attachments(self):
        page = Page.objects.create(name='test', text='Testfoo', user=self.user)

        number_of_attachments = 100

        # create three attachments for `page`
        # they only need to be children („have page.name as prefix“) for `page`
        with open(join(BASE_PATH, self.FILE_HAPPY), 'rb') as happy:
            for i in range(number_of_attachments):
                name = '/'.join((page.name, 'attachment_' + str(i)))
                Page.objects.create(name=name,
                                    text='',
                                    user=self.user,
                                    attachment=File(happy),
                                    attachment_filename=happy.name + str(i))

        self.assertEqual(len(Page.objects.get_attachment_list(page.name)),
                         number_of_attachments)

        request = self.factory.get('/')
        request.user = self.user

        new_name = 'new_test'
        from inyoka.wiki.actions import _rename  # local import, as __getitem__ of storage uses ORM
        _rename(request, page, new_name)

        page.refresh_from_db()
        self.assertEqual(page.name, new_name)

        for p in Page.objects.get_attachment_list(page.name):
            self.assertTrue(p.startswith(page.name))
