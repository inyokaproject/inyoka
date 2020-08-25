# -*- coding: utf-8 -*-
"""
    tests.apps.portal.test_admin
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test some admin commands

    :copyright: (c) 2007-2020 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import io

from django.core import mail, management

from inyoka.portal.user import User
from inyoka.utils.test import TestCase


class TestAdminCommands(TestCase):

    def test_rename_users(self):
        User.objects.register_user("gandalf", "gandalf@hdr.de", "pwd", False)
        User.objects.register_user("saroman", "saroman@hdr.de", "pwd", False)
        rename_file = io.StringIO('[{"oldname":"gandalf", "newname":"thewhite"},{"oldname":"saroman", "newname":"thedead"}]')
        management.call_command("renameusers", file=rename_file, verbosity=0)
        self.assertEqual(str(User.objects.get_by_username_or_email("gandalf@hdr.de")), "thewhite")
        self.assertEqual(str(User.objects.get_by_username_or_email("saroman@hdr.de")), "thedead")
        self.assertFalse('thewhite' in mail.outbox[1].body)
        self.assertTrue('thedead' in mail.outbox[1].body)
