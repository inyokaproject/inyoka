from inyoka.default_settings import *
from os.path import join

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'ubuntuusers',
        'USER': 'root',
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
LOGIN_URL='//%s/login/' % BASE_DOMAIN_NAME
ADMIN_MEDIA_PREFIX = STATIC_URL + '/_admin/'
INYOKA_SYSTEM_USER_EMAIL = 'system@' + BASE_DOMAIN_NAME
INYOKA_CONTACT_EMAIL = '@'.join(['webteam', BASE_DOMAIN_NAME])


EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

SECRET_KEY = None

INSTALLED_APPS = INSTALLED_APPS + (
    'inyoka_theme_default',
)

# Django Debug Toolbar Integration
#
# uncomment to activate debug toolbar support
#MIDDLEWARE_CLASSES += ('debug_toolbar.middleware.DebugToolbarMiddleware',)
#INSTALLED_APPS += ('debug_toolbar',)
