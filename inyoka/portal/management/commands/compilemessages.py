#-*- coding: utf-8 -*-
"""
    inyoka.portal.management.commands.compilemessages
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides a command to the Django ``manage.py`` file to compile
    the ``.po`` language files to ``.mo`` files. The ``.mo`` files are placed
    in the same directory as the regarding ``.po`` files.

    :copyright: (c) 2011-2014 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from subprocess import call

from django.core.management.base import BaseCommand

APPS = ['forum', 'portal', 'wiki', 'ikhaya', 'pastebin', 'planet', 'markup']


class Command(BaseCommand):

    def handle(self, *args, **options):
        for app in APPS:
            call(['pybabel', 'compile', '-D', 'django', '-d',
                  'inyoka/%s/locale' % app, '-l', 'de_DE'])
        # global files
        call(['pybabel', 'compile', '-D', 'django', '-d',
              'inyoka/locale', '-l', 'de_DE'])
