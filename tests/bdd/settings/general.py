import os
from uuid import uuid1

from inyoka.default_settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': f'bdd_{uuid1()}',
        'USER': 'postgres',
        'HOST': '',
        'PORT': '',
    }
}

if os.environ.get('INYOKA_THEME') == 'theme-ubuntuusers':
    INSTALLED_APPS = INSTALLED_APPS + (
        'inyoka_theme_ubuntuusers',
    )

    from os.path import join
    THEME_PATH = join(BASE_PATH, '..', 'theme-ubuntuusers', 'inyoka_theme_ubuntuusers')
    STATICFILES_DIRS = [join(THEME_PATH, 'static'),  # let own theme take precedence, so files can be overwritten
                       ] + STATICFILES_DIRS
    TEMPLATES[1]['DIRS'].insert(0, join(THEME_PATH, 'jinja2'))

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
