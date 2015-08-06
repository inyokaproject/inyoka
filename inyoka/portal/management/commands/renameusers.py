# -*- coding: utf-8 -*-
"""
    inyoka.portal.management.commands.renameuser
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides a command to the Django ``manage.py`` file to rename
    a list of users defined by a JSON file as shown in the following example:
    [{"oldname":"user1", "newname":"kloss"},{"oldname":"user2", "newname":"spinne"}]
    If the optional parameter 'silent' is passed, no mails will be sent to the users
    :copyright: (c) 2011-2015 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import json

from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext as _

from inyoka.portal.user import User


class Command(BaseCommand):
    help = "Rename all users as specified in the given JSON file"
    args = '<rename.json> [silent]'

    def handle(self, *args, **options):
        if len(args) == 0:
            raise CommandError(_(u"Error: No JSON file specified!"))
        notify = "silent" not in args
        if isinstance(args[0], basestring):
            with open(args[0]) as json_file:
                data = json.load(json_file)
        else:
            data = json.load(args[0])
        for username in data:
            try:
                user = User.objects.get_by_username_or_email(username["oldname"])
            except User.DoesNotExist:
                self.stderr.write(_(u"User '{oldname}' does not exist. Skipping...").format(oldname=username["oldname"]))
            else:
                try:
                    if not user.rename(username["newname"], notify):
                        self.stderr.write(_(u"User name '{newname}' already exists. Skipping...").format(newname=username["newname"]))
                except ValueError:
                    self.stderr.write(_(u"New user name '{newname}' contains invalid characters. Skipping...").format(newname=username["newname"]))
        self.stdout.write(_(u"Renaming users complete."))
