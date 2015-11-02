# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('forum', '0004_remove_welcomemessage_rendered_text_old'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='postrevision',
            name='post',
        ),
        migrations.DeleteModel(
            name='PostRevision',
        ),
        migrations.RemoveField(
            model_name='post',
            name='has_revision',
        ),
        migrations.RemoveField(
            model_name='post',
            name='text',
        ),
    ]
