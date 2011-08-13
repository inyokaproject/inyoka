from subprocess import call

from django.core.management.base import BaseCommand

APPS = ['forum', 'portal', 'wiki', 'ikhaya', 'utils', 'pastebin', 'planet']

class Command(BaseCommand):

    def handle(self, *args, **options):
        for app in APPS:
            call(['pybabel', 'extract', '-F', 'extra/babel.cfg', '-o',
                  'inyoka/%s/locale/django.pot' % app, 'inyoka/%s' % app])
            call(['pybabel', 'update', '-D', 'django', '-i',
                  'inyoka/%s/locale/django.pot' % app, '-d',
                  'inyoka/%s/locale' % app, '-l', 'de'])
