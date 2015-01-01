#-*- coding: utf-8 -*-
"""
    inyoka.portal.management.commands.create_superuser
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides a command to the Django ``manage.py`` file to add a
    new user to the user table with full permissions on all forums that exist
    and will all rights to modify e.g. users or user content (e.g forum,
    ikhaya, wiki, etc.)

    :copyright: (c) 2011-2015 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from getpass import getpass
from optparse import make_option

from django.core.management.base import BaseCommand

from inyoka.forum.acl import join_flags, PRIVILEGES_DETAILS
from inyoka.forum.models import Forum, Privilege
from inyoka.portal.user import User, PERMISSION_NAMES


class Command(BaseCommand):
    help = "Create a user with all priviliges"

    option_list = BaseCommand.option_list + (
        make_option('-u', '--username', action='store',
                    default=None, dest='username'),
        make_option('-e', '--email', action='store',
                    default=None, dest='email'),
        make_option('-p', '--password', action='store',
                    default=None, dest='password')
    )

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']
        while not username:
            username = raw_input('username: ')
        while not email:
            email = raw_input('email: ')
        if not password:
            while not password:
                password = getpass('password: ')
                if password:
                    if password == getpass('repeat: '):
                        break
                    password = ''
        user = User.objects.register_user(username, email, password, False)
        permissions = 0
        for perm in PERMISSION_NAMES.keys():
            permissions |= perm
        user._permissions = permissions
        user.save()
        bits = dict(PRIVILEGES_DETAILS).keys()
        bits = join_flags(*bits)
        for forum in Forum.objects.all():
            Privilege(user=user, forum=forum, positive=bits, negative=0).save()
        print 'created superuser'
