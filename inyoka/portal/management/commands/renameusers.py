# -*- coding: utf-8 -*-
"""
    inyoka.portal.management.commands.renameuser
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides a command to the Django ``manage.py`` file to rename
    a list of users defined by a JSON file as shown in the following example:
    [{"oldname":"user1", "newname":"kloss"},{"oldname":"user2", "newname":"spinne"}]
    If the optional parameter '--silent' or '-s' is passed, no mails will be sent to the users
    :copyright: (c) 2011-2020 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import json

from django.core.management.base import BaseCommand
from django.utils.translation import ugettext as _

from inyoka.portal.user import User


class Command(BaseCommand):
    help = "Rename all users as specified in the given JSON file, "\
        + "using the fromat [{'oldname': 'Kevin', 'newname': 'Max'}, "\
        + "{'oldname': 'schaklin@web.de', 'newname': 'Anna'}]"

    def add_arguments(self, parser):
        parser.add_argument('-f', '--file',
            action="store",
            dest="json",
            # required=True, # would make sense, but breaks the test
            help="JSON file containing the list of users to rename and their new names")
        parser.add_argument('-s', '--silent',
            action="store_false",
            dest="notify",
            default=True,
            help="Does not send notification mails to renamed users")

    def handle(self, **options):
        """
        Opens a json file and renames each user specified by the file.

        The json format has to be a list of objects, where any object has the
        attributes 'oldname' and 'newname'.

        'oldname' can also be an E-Mail adress of a user.

        For Example:

        [{'oldname': 'Kevin', 'newname': 'Max'},
        {'oldname': 'schaklin@web.de', 'newname': 'Anna'}]

        The file argument can be either a path to a json file or a python file
        object pointing to a json file.
        """
        notify = options['notify']
        verbosity = int(options['verbosity'])
        rename_file = options['json']
        if rename_file is None:
            self.stderr.write(_("No JSON file specified. Aborting..."))
            return
        if isinstance(rename_file, str):
            with open(rename_file) as json_file:
                data = json.load(json_file)
        else:
            data = json.load(rename_file)

        for username in data:
            if verbosity >= 2:
                self.stdout.write(_("Renaming {oldname} to {newname}...").format(
                    oldname=username["oldname"],
                    newname=username["newname"]))
            try:
                user = User.objects.get_by_username_or_email(username["oldname"])
            except User.DoesNotExist:
                self.stderr.write(_("User '{oldname}' does not exist. Skipping...").format(
                    oldname=username["oldname"]))
            else:
                try:
                    vacant = user.rename(username["newname"], notify)
                except ValueError:
                    self.stderr.write(_("New user name '{newname}' contains invalid characters. Skipping...").format(
                        newname=username["newname"]))
                else:
                    if not vacant:
                        self.stderr.write(_("User name '{newname}' already exists. Skipping...").format(
                            newname=username["newname"]))
        if verbosity >= 1:
            self.stdout.write(_("Renaming users complete."))
