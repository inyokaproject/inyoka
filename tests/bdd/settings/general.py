from inyoka.default_settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'bdd',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

INSTALLED_APPS = INSTALLED_APPS + (
    'inyoka_theme_ubuntuusers',
    'behave_django'
)

# debug settings
DEBUG = DEBUG_PROPAGATE_EXCEPTIONS = True

ALLOWED_HOSTS = ['.localhost']

# url settings

BASE_DOMAIN_NAME = 'ubuntuusers.local:8888'
INYOKA_URI_SCHEME = 'http'
SESSION_COOKIE_DOMAIN = '.ubuntuusers.local'
MEDIA_URL = '//media.%s/' % BASE_DOMAIN_NAME
STATIC_URL = '//static.%s/' % BASE_DOMAIN_NAME
LOGIN_URL='//%s/login/' % BASE_DOMAIN_NAME
ADMIN_MEDIA_PREFIX = STATIC_URL + '/_admin/'
INYOKA_SYSTEM_USER_EMAIL = 'system@' + BASE_DOMAIN_NAME
INYOKA_CONTACT_EMAIL = '@'.join(['webteam', BASE_DOMAIN_NAME])
INYOKA_HOST_STATICS = True

# Language code
LANGUAGE_CODE = 'de-DE'

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

SECRET_KEY = 'bdd_test_key'

HEADLESS = False
