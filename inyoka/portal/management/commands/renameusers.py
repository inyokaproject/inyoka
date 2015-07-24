# -*- coding: utf-8 -*-
"""
    inyoka.portal.management.commands.renameuser
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides a command to the Django ``manage.py`` file to rename
    a list of users defined by a JSON file as shown in the following example:
    [{"oldname":"user1", "newname":"kloss"},{"oldname":"user2", "newname":"spinne"}]
    
    :copyright: (c) 2011-2015 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.core.management.base import BaseCommand
from django.utils.translation import ugettext as _
from inyoka.portal.user import User
import json

class Command(BaseCommand):
    help = "Rename all users as specified in the given JSON file"
    args = '<rename.json>'
    
    def handle(self, *args, **options):
        if len(args) == 0:
            self.stderr.write(_(u"Error: No JSON file specified!"))
            return       
        
        with open(args[0]) as json_file:
            data = json.load(json_file)
        
        for username in data:
            try:
                user = User.objects.get_by_username_or_email(username["oldname"])
            except User.DoesNotExist:
                self.stderr.write(_(u"User '{oldname}' does not exist. Skipping...").format(oldname=username["oldname"]))
            else:
                try:
                    if not user.rename(username["newname"]):
                        self.stderr.write(_(u"User name '{newname}' already exists. Skipping...").format(newname=username["newname"]))
                except ValueError:
                    self.stderr.write(_(u"New user name '{newname}' contains invalid characters. Skipping...").format(newname=username["newname"]))
