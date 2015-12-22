from uuid import uuid1

from .base import *  # noqa

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'inyoka_{}'.format(uuid1()),
        'USER': 'root',
        'HOST': test_host,
    }
}
