# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0014_remove_groups'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='_permissions',
        ),
    ]
