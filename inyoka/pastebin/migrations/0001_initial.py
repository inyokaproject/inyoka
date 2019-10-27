# -*- coding: utf-8 -*-


import datetime

from django.db import migrations, models

import inyoka.utils.database


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Entry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=40, verbose_name='Title')),
                ('lang', models.CharField(max_length=20, verbose_name='Language')),
                ('code', inyoka.utils.database.PygmentsField(application='pastebin')),
                ('rendered_code_old', models.TextField(verbose_name='Rendered code', db_column='rendered_code')),
                ('pub_date', models.DateTimeField(default=datetime.datetime.utcnow, verbose_name='Date', db_index=True)),
                ('referrer', models.TextField(verbose_name='Referencing pages', blank=True)),
            ],
            options={
                'ordering': ('-id',),
                'verbose_name': 'Entry',
                'verbose_name_plural': 'Entries',
            },
            bases=(models.Model,),
        ),
    ]
