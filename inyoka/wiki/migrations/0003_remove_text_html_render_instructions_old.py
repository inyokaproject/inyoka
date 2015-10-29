# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0002_auto_20151027_2210'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='text',
            name='html_render_instructions_old',
        ),
    ]
