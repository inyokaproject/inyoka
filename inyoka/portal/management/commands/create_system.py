# -*- coding: utf-8 -*-
"""
    inyoka.portal.management.commands.create_superuser
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides a command to the Django ``manage.py`` file to add a
    new user to the user table with full permissions on all forums that exist
    and will all rights to modify e.g. users or user content (e.g forum,
    ikhaya, wiki, etc.)

    :copyright: (c) 2011-2016 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import print_function

from django.core.management.base import BaseCommand
from django.conf import settings

from inyoka.portal.user import User, Group


class Command(BaseCommand):
    help = "Create System Users and Groups"


    def handle(self, *args, **options):
        print('creating system groups...')
        Group.objects.create_system_groups()
        print('creating system users...')
        User.objects.create_system_users()
