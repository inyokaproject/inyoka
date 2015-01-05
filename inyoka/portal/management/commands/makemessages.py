# -*- coding: utf-8 -*-
"""
    inyoka.portal.management.commands.makemessages
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides a command to the Django ``manage.py`` file to create
    the ``.po`` language files out of the Python and template files. The actual
    output files are written to ``inyoka/APP/locale/lang_CODE/django.po`` and
    the regarding ``.pot`` file to ``inyoka/APP/django.pot``.

    :copyright: (c) 2011-2015 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from os import path
from subprocess import call

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.importlib import import_module

APPS = ['forum', 'portal', 'wiki', 'ikhaya', 'pastebin', 'planet', 'markup']


class Command(BaseCommand):

    def handle(self, *args, **options):
        for app in APPS:
            call(['pybabel', 'extract', '-F', 'extra/babel.cfg', '-k', '_',
                  '-k', 'gettext', '-k', 'pgettext:1c,2', '-k', 'ugettext',
                  '-k', 'ugettext_lazy', '-k', 'ungettext_lazy', '-o',
                  'inyoka/%s/locale/django.pot' % app, 'inyoka/%s' % app])
            call(['pybabel', 'update', '-D', 'django', '-i',
                  'inyoka/%s/locale/django.pot' % app, '-d',
                  'inyoka/%s/locale' % app, '-l', 'de_DE'])
        # global files
        call(['pybabel', 'extract', '-F', 'extra/babel.cfg', '-k', '_', '-k',
              'gettext', '-k', 'pgettext:1c,2', '-k', 'ugettext', '-k',
              'ugettext_lazy', '-k', 'ungettext_lazy', '-o',
              'inyoka/locale/django.pot', 'inyoka/utils', 'inyoka/middlewares'])
        call(['pybabel', 'update', '-D', 'django', '-i',
              'inyoka/locale/django.pot', '-d', 'inyoka/locale', '-l',
              'de_DE'])

        self._make_theme_messages()

    def _make_theme_messages(self):
        for app in settings.INSTALLED_APPS:
            module = import_module(app)
            if hasattr(module, 'INYOKA_THEME') and module.INYOKA_THEME == app:
                base_path = module.__path__[0]
                locale_dir = path.join(base_path, 'locale')
                template_dir = path.join(base_path, 'templates')
                call(['pybabel', 'extract', '-F', 'extra/babel.cfg', '-k', '_', '-k',
                    'gettext', '-k', 'pgettext:1c,2', '-k', 'ugettext', '-k',
                    'ugettext_lazy', '-k', 'ungettext_lazy', '-o',
                    path.join(locale_dir, 'django.pot'), template_dir])
                call(['pybabel', 'update', '-D', 'django', '-i',
                    path.join(locale_dir, 'django.pot'), '-d', locale_dir, '-l',
                    'de_DE'])
