from uuid import uuid1

from .base import *  # noqa

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'inyoka_{}'.format(uuid1()),
        'USER': 'postgres',
    }
}
