"""
    inyoka.portal.management.commands.create_superuser
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides a command to the Django ``manage.py`` file to add a
    new user to the user table with full permissions on all forums that exist
    and will all rights to modify e.g. users or user content (e.g. forum,
    ikhaya, wiki, etc.)

    :copyright: (c) 2011-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""


from getpass import getpass

from django.core.management.base import BaseCommand
from django.db import transaction

from inyoka.portal.user import User


class Command(BaseCommand):
    help = "Create a user with all privileges"

    def add_arguments(self, parser):
        parser.add_argument('-u', '--username', action='store', default=None, dest='username')
        parser.add_argument('-e', '--email', action='store', default=None, dest='email')
        parser.add_argument('-p', '--password', action='store', default=None, dest='password')

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']
        while not username:
            username = input('username: ')
        while not email:
            email = input('email: ')
        if not password:
            while not password:
                password = getpass('password: ')
                if password:
                    if password == getpass('repeat: '):
                        break
                    password = ''
        with transaction.atomic():
            user = User.objects.register_user(username, email, password, False)
            user.is_superuser = True
            user.save()
            print('created superuser')
