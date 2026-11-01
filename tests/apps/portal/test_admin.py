"""
tests.apps.portal.test_admin
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test some admin commands

:copyright: (c) 2007-2026 by the Inyoka Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

import io
import json
from argparse import ArgumentParser
from unittest.mock import patch

from django.core import mail, management

from inyoka.portal.management.commands.renameusers import Command
from inyoka.portal.user import User
from inyoka.utils.test import TestCase


class TestRenameUsersCommand(TestCase):
    def test_rename_users(self):
        User.objects.register_user('gandalf', 'gandalf@hdr.de', 'pwd', False)
        User.objects.register_user('saroman', 'saroman@hdr.de', 'pwd', False)
        rename_file = io.StringIO(
            '[{"oldname":"gandalf", "newname":"thewhite"},{"oldname":"saroman", "newname":"thedead"}]'
        )
        management.call_command('renameusers', file=rename_file, verbosity=0)
        self.assertEqual(
            str(User.objects.get_by_username_or_email('gandalf@hdr.de')), 'thewhite'
        )
        self.assertEqual(
            str(User.objects.get_by_username_or_email('saroman@hdr.de')), 'thedead'
        )
        self.assertFalse('thewhite' in mail.outbox[1].body)
        self.assertTrue('thedead' in mail.outbox[1].body)

    def test_add_arguments(self):
        parser = ArgumentParser()
        Command().add_arguments(parser)

        parsed = parser.parse_args(['-f', '/tmp/users.json', '-s'])
        self.assertEqual(parsed.json, '/tmp/users.json')
        self.assertFalse(parsed.notify)

    def test_handle_missing_file(self):
        command = Command()
        command.stdout = io.StringIO()
        command.stderr = io.StringIO()

        command.handle(json=None, notify=True, verbosity=1)

        self.assertEqual('', command.stdout.getvalue())
        self.assertIn('No JSON file specified. Aborting...', command.stderr.getvalue())

    def test_handle_rename_user_from_json(self):
        User.objects.create_user('old_user', 'old@example.test', 'pass')

        json_to_rename = io.StringIO(
            json.dumps(
                [
                    {'oldname': 'old_user', 'newname': 'new_user'},
                ]
            )
        )

        command = Command()
        command.stdout = io.StringIO()
        command.stderr = io.StringIO()
        command.handle(json=json_to_rename, notify=False, verbosity=2)

        self.assertIn('Renaming old_user to new_user...', command.stdout.getvalue())

    def test_handle_rename_not_existing_user(self):
        json_to_rename = io.StringIO(
            json.dumps(
                [
                    {'oldname': 'ghost', 'newname': 'missing_user'},
                ]
            )
        )

        command = Command()
        command.stdout = io.StringIO()
        command.stderr = io.StringIO()
        command.handle(json=json_to_rename, notify=True, verbosity=2)

        self.assertIn(
            "User 'ghost' does not exist. Skipping...", command.stderr.getvalue()
        )

    def test_handle_invalid_new_name(self):
        User.objects.create_user('bad_user', 'bad@example.test', 'pass')

        json_to_rename = io.StringIO(
            json.dumps(
                [
                    {'oldname': 'bad_user', 'newname': 'invalid?user'},
                ]
            )
        )

        command = Command()
        command.stdout = io.StringIO()
        command.stderr = io.StringIO()
        command.handle(json=json_to_rename, notify=True, verbosity=2)

        self.assertIn(
            "New user name 'invalid?user' contains invalid characters. Skipping...",
            command.stderr.getvalue(),
        )

    def test_handle_renames_already_taken_username(self):
        User.objects.create_user('occupied_name', 'occupied@example.test', 'pass')
        User.objects.create_user('second_old', 'second-old@example.test', 'pass')

        json_to_rename = io.StringIO(
            json.dumps(
                [
                    {'oldname': 'second_old', 'newname': 'occupied_name'},
                ]
            )
        )

        command = Command()
        command.stdout = io.StringIO()
        command.stderr = io.StringIO()

        command.handle(json=json_to_rename, notify=True, verbosity=2)

        self.assertIn(
            "User name 'occupied_name' already exists. Skipping...",
            command.stderr.getvalue(),
        )

    def test_handle_uses_file_object_and_does_not_send_mail_when_silent(self):
        User.objects.create_user('file_user', 'file@example.test', 'pass')

        command = Command()
        command.stdout = io.StringIO()
        command.stderr = io.StringIO()

        json_str = io.StringIO(
            json.dumps(
                [
                    {'oldname': 'file_user', 'newname': 'silent_user'},
                ]
            )
        )

        with patch.object(
            User, 'rename', autospec=True, return_value=True
        ) as mock_rename:
            command.handle(json=json_str, notify=False, verbosity=1)

        self.assertTrue(mock_rename.called)
        self.assertEqual(mock_rename.call_args.args[0].username, 'file_user')
        self.assertEqual(mock_rename.call_args.args[1], 'silent_user')
        self.assertFalse(mock_rename.call_args.args[2])
        self.assertIn('Renaming users complete.', command.stdout.getvalue())
