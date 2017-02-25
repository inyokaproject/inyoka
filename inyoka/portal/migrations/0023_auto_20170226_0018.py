# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0022_auto_20170117_1828'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='icon',
            field=models.FilePathField(blank=True, path=b'inyoka/inyoka/media/portal/team_icons', null=True, verbose_name='Group icon', match=b'.*\\.png'),
        ),
    ]
