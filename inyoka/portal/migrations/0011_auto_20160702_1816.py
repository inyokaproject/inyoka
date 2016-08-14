# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

def postgresql_drop_indexes(apps, schema_editor):
    if schema_editor.connection.vendor.startswith('postgre'):
        schema_editor.execute('DROP INDEX portal_user_groups_e8701ad4;')
        schema_editor.execute('DROP INDEX portal_user_groups_0e939a4f;')

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
        migrations.RunPython(postgresql_drop_indexes),
    ]
