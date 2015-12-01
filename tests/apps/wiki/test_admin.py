# -*- coding: utf-8 -*-
"""
    tests.apps.wiki.test_admin
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test some admin commands

    :copyright: (c) 2007-2015 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.core import management

from inyoka.utils.test import TestCase


class TestAdminCommands(TestCase):

    def test_generate_static_wiki(self):
        management.call_command("generate_static_wiki", verbosity=0, path="test_static_wiki")

    def tearDown(self):
        import shutil
        shutil.rmtree("test_static_wiki")
