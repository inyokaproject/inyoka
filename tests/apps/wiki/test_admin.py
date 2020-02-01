# -*- coding: utf-8 -*-
"""
    tests.apps.wiki.test_admin
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test some admin commands

    :copyright: (c) 2007-2020 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from shutil import rmtree

from django.conf import settings
from django.core import management

from inyoka.portal.user import User
from inyoka.portal.models import StaticPage
from inyoka.utils.test import TestCase
from inyoka.wiki.models import Page


class TestAdminCommands(TestCase):

    def setUp(self):
        user = User.objects.create_user('test_user', 'test2@inyoka.local')
        Page.objects.create(name='test', text='Testfoo', user=user, attachment=None, attachment_filename=None)

        StaticPage.objects.create(key='lizenz', title='Lizenz', content='(c) Meine Lizenz')

        rmtree(settings.STATIC_ROOT, ignore_errors=True)
        management.call_command('collectstatic', '--noinput', '--link', verbosity=0)

    def tearDown(self):
        rmtree('test_static_wiki')

    def test_generate_static_wiki(self):
        management.call_command('generate_static_wiki', verbosity=0, path='test_static_wiki')

