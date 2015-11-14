from .base import *  # noqa

CACHES['content']['KEY_PREFIX'] = 'test-sqlite'
CACHES['default']['KEY_PREFIX'] = 'test-sqlite'
