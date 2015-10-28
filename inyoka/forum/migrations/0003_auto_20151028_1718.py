# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forum', '0002_auto_20151016_1603'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='post',
            name='rendered_text_old',
        ),
        migrations.RemoveField(
            model_name='welcomemessage',
            name='rendered_text_old',
        ),
        migrations.AlterField(
            model_name='topic',
            name='slug',
            field=models.CharField(db_index=True, max_length=50, blank=True),
            preserve_default=True,
        ),
    ]
