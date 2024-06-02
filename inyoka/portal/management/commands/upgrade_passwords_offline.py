"""
    inyoka.portal.management.commands.upgrade_passwords_offline
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides a command to the Django ``manage.py`` file to upgrade older passwords to a newer hashing method.
    By wrapping the old password hash, it does not require a login from a user.

    see https://docs.djangoproject.com/en/4.2/topics/auth/passwords/#password-upgrading-without-requiring-a-login

    :copyright: (c) 2011-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import traceback

from django.core.management.base import BaseCommand

from inyoka.portal.user import User
from inyoka.utils.user import PBKDF2WrappedSHA1PasswordHasher


class Command(BaseCommand):
    help = "Upgrade older passwords to a newer hashing method (by wrapping it)"

    def _wrap_sha1_passwords(self):
        users = User.objects.filter(password__startswith="sha1")

        if len(users) == 0:
            print('No users with sha1 password-hashes found')

        hasher = PBKDF2WrappedSHA1PasswordHasher()
        for user in users:
            try:
                _algorithm, salt, sha1_hash = user.password.split("$", 2)
                user.password = hasher.encode_sha1_hash(sha1_hash, salt)
            except Exception as e:
                print(f'Skipping user {user}, as an error occurred. Traceback was:')
                print(traceback.format_exc())
                continue

            user.save(update_fields=["password"])

    def handle(self, *args, **options):
        self._wrap_sha1_passwords()
