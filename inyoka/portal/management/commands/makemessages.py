# -*- coding: utf-8 -*-
"""
    inyoka.portal.management.commands.makemessages
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides a command to the Django ``manage.py`` file to create
    the ``.po`` language files out of the Python and template files. The actual
    output files are written to ``inyoka/APP/locale/lang_CODE/django.po`` and
    the regarding ``.pot`` file to ``inyoka/APP/django.pot``.

    :copyright: (c) 2011-2023 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from os import path
from subprocess import call

from django.apps import apps
from django.core.management.base import BaseCommand

from inyoka import INYOKA_VERSION

APPS = ['forum', 'portal', 'wiki', 'ikhaya', 'pastebin', 'planet', 'markup']


class Command(BaseCommand):

    def handle(self, *args, **options):
        babel_cfg_path = path.abspath('extra/babel.cfg')
        args_extract = [
            'pybabel', 'extract', '-F', babel_cfg_path,
            '-k', '_', '-k', 'gettext', '-k', 'pgettext:1c,2',
            '-k', 'gettext_lazy', '-k', 'ngettext_lazy',
            '--no-wrap', '--no-location', '--sort-output',
            '--copyright-holder=Inyoka Team (see AUTHORS)',
            '--project=Inyoka Project', '--version=' + INYOKA_VERSION
        ]
        args_update = ['pybabel', 'update', '-D', 'django', '-l', 'de_DE',
                       '--no-wrap']

        for app in APPS:
            args = args_extract + [
                '-o', 'inyoka/%s/locale/django.pot' % app,
                'inyoka/%s' % app
            ]
            call(args)
            args = args_update + [
                '-i', 'inyoka/%s/locale/django.pot' % app,
                '-d', 'inyoka/%s/locale' % app,
            ]
            call(args)
        # global files
        args = args_extract + [
            '-o', 'inyoka/locale/django.pot',
            'inyoka/utils', 'inyoka/middlewares'
        ]
        call(args)
        args = args_update + [
            '-i', 'inyoka/locale/django.pot',
            '-d', 'inyoka/locale',
        ]
        call(args)

        self._make_theme_messages(args_extract, args_update)

    def _make_theme_messages(self, args_extract, args_update):
        for app in apps.get_app_configs():
            module = app.module
            if hasattr(module, 'INYOKA_THEME'):
                base_path = module.__path__[0]
                cwd = path.normpath(path.join(base_path, '..'))
                basename = path.basename(base_path)
                locale_dir = path.join(basename, 'locale')
                template_dir = path.join(basename, 'jinja2')
                args = args_extract + [
                    '-o', path.join(locale_dir, 'django.pot'),
                    template_dir,
                ]
                call(args, cwd=cwd)
                args = args_update + [
                    '-i', path.join(locale_dir, 'django.pot'),
                    '-d', locale_dir,
                ]
                call(args, cwd=cwd)
