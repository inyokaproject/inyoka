from uuid import uuid1

from .base import *  # noqa

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'inyoka_{}'.format(uuid1()),
        'USER': 'postgres',
        'HOST': test_host,
    }
}

TEST_OUTPUT_FILE_NAME = 'postgresql.xml'
