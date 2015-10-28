# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pastebin', '0002_entry_author'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='entry',
            name='rendered_code_old',
        ),
    ]
