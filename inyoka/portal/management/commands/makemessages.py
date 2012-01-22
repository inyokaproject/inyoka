from subprocess import call

from django.core.management.base import BaseCommand

APPS = ['forum', 'portal', 'wiki', 'ikhaya', 'pastebin', 'planet']


class Command(BaseCommand):

    def handle(self, *args, **options):
        for app in APPS:
            call(['pybabel', 'extract', '-F', 'extra/babel.cfg', '-o',
                  'inyoka/%s/locale/django.pot' % app, 'inyoka/%s' % app])
            call(['pybabel', 'update', '-D', 'django', '-i',
                  'inyoka/%s/locale/django.pot' % app, '-d',
                  'inyoka/%s/locale' % app, '-l', 'de_DE'])
        # global files
        call(['pybabel', 'extract', '-F', 'extra/babel.cfg', '-o',
              'inyoka/locale/django.pot', 'inyoka/templates', 'inyoka/utils'])
        call(['pybabel', 'update', '-D', 'django', '-i',
              'inyoka/locale/django.pot', '-d',
              'inyoka/locale', '-l', 'de_DE'])
