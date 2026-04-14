"""
    inyoka
    ~~~~~~

    Init file for the inyoka portal.

    :copyright: (c) 2007-2026 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from .celery_app import app as celery_app  # noqa

# Inyoka version is updated through bumpversion and can stay hardcoded here.
INYOKA_VERSION = "1.52.9"
