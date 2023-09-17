from inyoka import INYOKA_VERSION
from inyoka.default_settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'ubuntuusers',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

# debug settings
DEBUG = DEBUG_PROPAGATE_EXCEPTIONS = True

ALLOWED_HOSTS = ['.ubuntuusers.local']

# url settings
BASE_DOMAIN_NAME = 'ubuntuusers.local:8080'
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

SECRET_KEY = None

INSTALLED_APPS = INSTALLED_APPS + (
    'inyoka_theme_default',
)

# Sentry integration
# remove commment to enable sentry integration
# insert DSN for used sentry instance
"""
import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn=None,  # TODO: adapt to instance
    integrations=[DjangoIntegration(), CeleryIntegration()],
    traces_sample_rate=1.0,
    #send_default_pii=True,  # uncomment, if personal data in sentry is ok
    release=INYOKA_VERSION,
    environment="production"
)
"""

# Django Debug Toolbar Integration
#
# uncomment to activate debug toolbar support
#MIDDLEWARE += ('debug_toolbar.middleware.DebugToolbarMiddleware',)
#INSTALLED_APPS += ('debug_toolbar',)
