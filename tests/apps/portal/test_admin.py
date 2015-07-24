#-*- coding: utf-8 -*-
"""
    tests.apps.portal.test_user
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test some user model functions

    :copyright: (c) 2007-2015 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from inyoka.portal.management.commands.renameusers import Command
from django.test import TestCase
import StringIO

class TestAdminCommands(TestCase):

    def test_rename_users(self):
        output = StringIO.StringIO('[{"oldname":"user1", "newname":"kloss"},{"oldname":"user2", "newname":"spinne"}]')
        com = Command()
        com.handle(*[output],**{})