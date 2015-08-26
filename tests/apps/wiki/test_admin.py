#-*- coding: utf-8 -*-
"""
    tests.apps.portal.test_user
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tests the wiki apps admin commands

    :copyright: (c) 2007-2015 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.core import management
from django.test import TestCase


class TestAdminCommands(TestCase):

    def test_rename_users(self):
        management.call_command("generate_static_wiki")
        # TODO Test Admin Command generate_static_wiki
