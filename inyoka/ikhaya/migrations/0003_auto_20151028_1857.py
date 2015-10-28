# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ikhaya', '0002_auto_20151016_1603'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='comment',
            name='rendered_text_old',
        ),
        migrations.RemoveField(
            model_name='report',
            name='rendered_text_old',
        ),
    ]
