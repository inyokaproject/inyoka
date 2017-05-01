# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forum', '0012_django_permissions'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='topic',
            options={'ordering': ['id'], 'verbose_name': 'Topic', 'verbose_name_plural': 'Topics', 'permissions': (('manage_reported_topic', 'Can manage reported Topics'),)},
        ),
    ]
