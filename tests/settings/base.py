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

# explicitly add tests.utils to apps to run unittests here
INSTALLED_APPS = INSTALLED_APPS + (
    'tests.utils',
    'inyoka_theme_ubuntuusers',
)

SECRET_KEY = 'test-secret-key'

INYOKA_AKISMET_KEY = 'inyokatestkey'
INYOKA_AKISMET_URL = 'http://testserver/'

CACHES['content']['LOCATION'] = 'redis://{}:6379/0'.format(test_host or 'localhost')
CACHES['content']['KEY_PREFIX'] = str(uuid1())

CACHES['default']['LOCATION'] = 'redis://{}:6379/1'.format(test_host or 'localhost')
CACHES['default']['KEY_PREFIX'] = str(uuid1())

BROKER_URL = 'redis://{}:6379/0'.format(test_host or 'localhost')
CELERY_RESULT_BACKEND = 'redis://{}:6379/0'.format(test_host or 'localhost')
