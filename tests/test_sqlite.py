from inyoka.default_settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '',
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
SESSION_COOKIE_DOMAIN = '.ubuntuusers.local'
MEDIA_URL = 'http://media.%s' % BASE_DOMAIN_NAME
STATIC_URL = 'http://static.%s' % BASE_DOMAIN_NAME
ADMIN_MEDIA_PREFIX = STATIC_URL + '/_admin/'
INYOKA_SYSTEM_USER_EMAIL = 'system@' + BASE_DOMAIN_NAME
GOOGLE_MAPS_APIKEY = 'ABQIAAAAnGRs_sYisCDW3FXIZAzZ9RR0WYmUN-JWdjE121Rerp-F3KIi4BQQM-N93TqupJwysf0dHBu_LfF6AQ'

SEARCH_NODES = ['127.0.0.1:9500']

# WORKAROUND for fancy django-nose that does not yet load models in tests properly
INSTALLED_APPS = list(INSTALLED_APPS) + ['inyoka.utils.tests']

SEARCH_NODES = ['127.0.0.1:9200']
