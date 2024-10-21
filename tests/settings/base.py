import os
from uuid import uuid1

from inyoka.default_settings import *  # NOQA

try:
    from .custom import test_host
except ImportError:
    # The file custom.py is optional. If it does not exist, then use an empty
    # string test_host.
    test_host = ''

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

# debug settings
DEBUG = DEBUG_PROPAGATE_EXCEPTIONS = True

# url settings
ALLOWED_HOSTS = ['.ubuntuusers.local']
BASE_DOMAIN_NAME = 'ubuntuusers.local:8080'
INYOKA_URI_SCHEME = 'http'
SESSION_COOKIE_DOMAIN = '.ubuntuusers.local'
MEDIA_URL = '//media.%s/' % BASE_DOMAIN_NAME
STATIC_URL = '//static.%s/' % BASE_DOMAIN_NAME
ADMIN_MEDIA_PREFIX = STATIC_URL + '/_admin/'
INYOKA_SYSTEM_USER_EMAIL = 'system@' + BASE_DOMAIN_NAME

# debug toolbar adds details like template-context, django does not by default
MIDDLEWARE += ('debug_toolbar.middleware.DebugToolbarMiddleware',)

INSTALLED_APPS = INSTALLED_APPS + (
    'tests.utils', # explicitly add tests.utils to apps to run unittests here
    'debug_toolbar',
)

if os.environ.get('INYOKA_THEME') == 'theme-ubuntuusers':
    INSTALLED_APPS = INSTALLED_APPS + (
        'inyoka_theme_ubuntuusers',
    )

    from os.path import join
    THEME_PATH = join(BASE_PATH, '..', 'theme-ubuntuusers', 'inyoka_theme_ubuntuusers')
    STATICFILES_DIRS = [join(THEME_PATH, 'static'),  # let own theme take precedence, so files can be overwritten
                       ] + STATICFILES_DIRS
    TEMPLATES[1]['DIRS'].insert(0, join(THEME_PATH, 'jinja2'))


SECRET_KEY = 'test-secret-key'

INYOKA_AKISMET_KEY = 'inyokatestkey'
INYOKA_AKISMET_URL = 'http://testserver/'

CACHES['content']['LOCATION'] = 'redis://{}:6379/0'.format(test_host or 'localhost')
CACHES['content']['KEY_PREFIX'] = str(uuid1())

CACHES['default']['LOCATION'] = 'redis://{}:6379/1'.format(test_host or 'localhost')
CACHES['default']['KEY_PREFIX'] = str(uuid1())

BROKER_URL = 'redis://{}:6379/0'.format(test_host or 'localhost')
CELERY_RESULT_BACKEND = 'redis://{}:6379/0'.format(test_host or 'localhost')
