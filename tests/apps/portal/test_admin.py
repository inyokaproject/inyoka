#-*- coding: utf-8 -*-
"""
    tests.apps.portal.test_user
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test some admin commands

    :copyright: (c) 2007-2015 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from inyoka.portal.user import User

from django.test import TestCase
from django.core import management
import StringIO


class TestAdminCommands(TestCase):

    def test_rename_users(self):
        User.objects.register_user("gandalf", "gandalf@hdr.de", "pwd", False)
        User.objects.register_user("saroman", "saroman@hdr.de", "pwd", False)
        output = StringIO.StringIO('[{"oldname":"gandalf", "newname":"thewhite"},{"oldname":"saroman", "newname":"thedead"}]')
        management.call_command("renameusers", *[output, "silent"])
        self.assertEqual(unicode(User.objects.get_by_username_or_email("gandalf@hdr.de")), "thewhite")
        self.assertEqual(unicode(User.objects.get_by_username_or_email("saroman@hdr.de")), "thedead")

# TODO: Check if send_email() uses correct data. www.heise.de/newsticker/meldung/Datenpanne-an-der-TU-Berlin-Rueckmeldeaufforderung-enthaelt-Daten-anderer-Studis-2671551.html
