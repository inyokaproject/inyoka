from .base import *  # noqa

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'inyoka_testrunner',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

CACHES['content']['KEY_PREFIX'] = 'test-mysql'
CACHES['default']['KEY_PREFIX'] = 'test-mysql'
