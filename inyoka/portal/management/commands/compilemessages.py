# -*- coding: utf-8 -*-
"""
    inyoka.portal.management.commands.compilemessages
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides a command to the Django ``manage.py`` file to compile
    the ``.po`` language files to ``.mo`` files. The ``.mo`` files are placed
    in the same directory as the regarding ``.po`` files.

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
        args_compile = ['pybabel', 'compile', '-D', 'django', '-l', 'de_DE']
        for app in APPS:
            args = args_compile + ['-d', 'inyoka/%s/locale' % app]
            call(args)
        # global files
        args = args_compile + ['-d', 'inyoka/locale']
        call(args)

        self._compile_theme_messages(args_compile)

    def _compile_theme_messages(self, args_compile):
        for app in settings.INSTALLED_APPS:
            module = import_module(app)
            if hasattr(module, 'INYOKA_THEME') and module.INYOKA_THEME == app:
                base_path = module.__path__[0]
                locale_dir = path.join(base_path, 'locale')
                args = args_compile + ['-d', locale_dir]
                call(args, cwd=base_path)
