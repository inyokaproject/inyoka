from django.db import models
from inyoka.utils.database import JSONField


class JSONEntry(models.Model):
    f = JSONField(blank=True)
