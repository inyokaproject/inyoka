# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pastebin', '0003_remove_entry_rendered_code_old'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='entry',
            options={'ordering': ('-id',), 'verbose_name': 'Entry', 'verbose_name_plural': 'Entries', 'permissions': (('view_entry', 'View Entry'),)},
        ),
    ]
