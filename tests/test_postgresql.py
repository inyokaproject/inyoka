from inyoka.default_settings import *
from test_sqlite import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'inyoka_testrunner',
    }
}
