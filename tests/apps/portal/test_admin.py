#-*- coding: utf-8 -*-
"""
    tests.apps.portal.test_user
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test some admin commands

    :copyright: (c) 2007-2015 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from inyoka.portal.management.commands.renameusers import Command
from inyoka.portal.user import User

from django.test import TestCase
import StringIO
from sys import stderr

class TestAdminCommands(TestCase):

    def test_rename_users(self):
        User.objects.register_user('gandalf', 'gandalf@hdr.de', 'pwd', False)
        User.objects.register_user('saroman', 'saroman@hdr.de', 'pwd', False)
        output = StringIO.StringIO('[{"oldname":"gandalf", "newname":"thewhite"},{"oldname":"saroman", "newname":"thedead"}]')        
        com = Command()
        com.stderr = stderr #FIXME: Workaround for a Django 1.5 bug. Should be removed after shifting to newer Django Version
        com.handle(*[output,"silent"],**{})
        
        self.assertEqual(User.objects.get_by_username_or_email("gandalf@hdr.de").__unicode__(),"thewhite")
        self.assertEqual(User.objects.get_by_username_or_email("saroman@hdr.de").__unicode__(),"thedead")