from inyoka.default_settings import *
from .base import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'inyoka_testrunner',
    }
}

try:
    from ._postgresql import *
except ImportError:
    pass
