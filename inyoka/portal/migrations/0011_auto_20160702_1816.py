# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0010_copy_groups'),
    ]

    operations = [
        migrations.RenameField(
            model_name='user',
            old_name='groups',
            new_name='groups_old',
        ),
    ]
