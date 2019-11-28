# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0026_remove_user_forum_last_read'),
    ]

    operations = [
        migrations.CreateModel(
            name='Linkmap',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('token', models.CharField(unique=True, max_length=128, verbose_name='Token', validators=[django.core.validators.RegexValidator(regex=b'^[a-z\\-_]+[1-9]*$', message='Only lowercase letters, - and _ allowed. Numbers as postfix.')])),
                ('url', models.URLField(verbose_name='Link')),
                ('icon', models.ImageField(upload_to=b'linkmap/icons', verbose_name='Icon', blank=True)),
            ],
        ),
    ]
