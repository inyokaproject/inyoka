# -*- coding: utf-8 -*-
"""
    inyoka.portal.management.commands.renameuser
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides a command to the Django ``manage.py`` file to rename
    a list of users defined by a JSON file as shown in the following example:
    [{"oldname":"user1", "newname":"kloss"},{"oldname":"user2", "newname":"spinne"}]
    If the optional parameter '--silent' or '-s' is passed, no mails will be sent to the users
    :copyright: (c) 2011-2015 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import json
from optparse import make_option

from django.core.management.base import LabelCommand
from django.utils.translation import ugettext as _

from inyoka.portal.user import User


class Command(LabelCommand):
    help = "Rename all users as specified in the given JSON file"
    label = "JSON file name"
    args = '<filename>'
    option_list = LabelCommand.option_list + (
        make_option('-s', '--silent',
            action="store_false", dest="notify", default=True,
            help="Does not send notification mails to renamed users"),
    )

    def handle_label(self, label, **options):
        """
        Opens a json-file and renames each user inside the file.

        The json-format has to be a list ob objects, where any object has the
        attributes 'oldname' and 'newname'.

        'oldname' can also be an E-Mail adress of a user.

        For Example:

        [{'oldname': 'Kevin', 'newname': 'Max'}, {'oldname': 'schaklin@web.de', 'newname': 'Anna'}]

        The argument label can be a path to a json-file or a python file
        object to a json-file.
        """
        notify = options.get('notify')
        verbosity = int(options.get('verbosity'))
        if isinstance(label, basestring):
            with open(label) as json_file:
                data = json.load(json_file)
        else:
            data = json.load(label)

        for username in data:
            if verbosity >= 2:
                self.stdout.write(_(u"Renaming {oldname} to {newname}...").format(
                    oldname=username["oldname"],
                    newname=username["newname"]))
            try:
                user = User.objects.get_by_username_or_email(username["oldname"])
            except User.DoesNotExist:
                self.stderr.write(_(u"User '{oldname}' does not exist. Skipping...").format(
                    oldname=username["oldname"]))
            else:
                try:
                    existed = user.rename(username["newname"], notify)
                except ValueError:
                    self.stderr.write(_(u"New user name '{newname}' contains invalid characters. Skipping...").format(
                        newname=username["newname"]))
                else:
                    if existed:
                        self.stderr.write(_(u"User name '{newname}' already exists. Skipping...").format(
                            newname=username["newname"]))
        if verbosity >= 1:
            self.stdout.write(_(u"Renaming users complete."))
