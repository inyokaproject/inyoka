from inyoka.default_settings import *
from .base import *

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

try:
    from ._mysql import *
except ImportError:
    pass
