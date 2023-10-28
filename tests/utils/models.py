"""
    tests.utils.models
    ~~~~~~~~~~~~~~~~~~

    Models that are only used within tests.

    :copyright: (c) 2011-2023 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.db import models

from inyoka.utils.database import JSONField


class JSONEntry(models.Model):
    f = JSONField(blank=True)
