from inyoka.default_settings import *  # NOQA

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

CACHES['content']['LOCATION'] = 'redis://127.0.0.1:6379/0'
CACHES['content']['KEY_PREFIX'] = 'inyoka-test'

CACHES['default']['LOCATION'] = 'redis://127.0.0.1:6379/1'
CACHES['default']['KEY_PREFIX'] = 'inyoka-test'
