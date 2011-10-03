from django.db import models
from inyoka.utils.database import JSONField, PickleField


class JSONEntry(models.Model):
    f = JSONField(blank=True)

class PickleEntry(models.Model):
    f = PickleField(blank=True)
