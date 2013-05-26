#-*- coding: utf-8 -*-
"""
    tests.utils.models
    ~~~~~~~~~~~~~~~~~~

    Models that are only used within tests.

    :copyright: (c) 2011-2013 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL.
"""
from django.db import models
from inyoka.utils.database import JSONField


class JSONEntry(models.Model):
    f = JSONField(blank=True)
