from uuid import uuid1

from .base import *  # noqa

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'inyoka_{}'.format(uuid1()),
        'USER': 'postgres',
        'HOST': test_host,
    }
}

# use redis databases starting from 10, so they do not infer with sqlite
CACHES['content']['LOCATION'] = 'redis://{}:6379/10'.format(test_host or 'localhost')
CACHES['default']['LOCATION'] = 'redis://{}:6379/11'.format(test_host or 'localhost')
BROKER_URL = 'redis://{}:6379/10'.format(test_host or 'localhost')
CELERY_RESULT_BACKEND = 'redis://{}:6379/10'.format(test_host or 'localhost')

TEST_OUTPUT_FILE_NAME = 'postgresql.xml'
