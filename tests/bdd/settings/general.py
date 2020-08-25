from uuid import uuid1

from inyoka.default_settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'bdd_{}'.format(uuid1()),
        'USER': 'postgres',
        'HOST': '',
        'PORT': '',
    }
}

INSTALLED_APPS = INSTALLED_APPS + (
    'inyoka_theme_ubuntuusers',
)

# debug settings
DEBUG = DEBUG_PROPAGATE_EXCEPTIONS = False


# url settings

ALLOWED_HOSTS = ['.ubuntuusers.local']
BASE_DOMAIN_NAME = 'ubuntuusers.local'
INYOKA_URI_SCHEME = 'http'
SESSION_COOKIE_DOMAIN = '.ubuntuusers.local'
MEDIA_URL = '//media.%s/' % BASE_DOMAIN_NAME
STATIC_URL = '//static.%s/' % BASE_DOMAIN_NAME
LOGIN_URL = '//%s/login/' % BASE_DOMAIN_NAME
ADMIN_MEDIA_PREFIX = STATIC_URL + '/_admin/'
INYOKA_SYSTEM_USER_EMAIL = 'system@' + BASE_DOMAIN_NAME
INYOKA_CONTACT_EMAIL = '@'.join(['webteam', BASE_DOMAIN_NAME])
INYOKA_HOST_STATICS = True

# Language code
LANGUAGE_CODE = 'de-DE'

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

SECRET_KEY = 'bdd_test_key'

# UI test settings
HEADLESS = False
