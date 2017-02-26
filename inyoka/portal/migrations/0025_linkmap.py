# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0024_auto_20170429_1526'),
    ]

    operations = [
        migrations.CreateModel(
            name='Linkmap',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('token', models.CharField(max_length=128, verbose_name='Token')),
                ('url', models.CharField(max_length=128, verbose_name='Link')),
            ],
        ),
    ]
