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
ADMIN_MEDIA_PREFIX = STATIC_URL + '/_admin/'
INYOKA_SYSTEM_USER_EMAIL = 'system@' + BASE_DOMAIN_NAME
INYOKA_CONTACT_EMAIL = '@'.join(['webteam', BASE_DOMAIN_NAME])
GOOGLE_MAPS_APIKEY = 'ABQIAAAAnGRs_sYisCDW3FXIZAzZ9RR0WYmUN-JWdjE121Rerp-F3KIi4BQQM-N93TqupJwysf0dHBu_LfF6AQ'


EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

SECRET_KEY = None

# Django Debug Toolbar Integration
#
# uncomment to activate debug toolbar support
#MIDDLEWARE_CLASSES += ('debug_toolbar.middleware.DebugToolbarMiddleware',)
#INSTALLED_APPS += ('debug_toolbar',)
