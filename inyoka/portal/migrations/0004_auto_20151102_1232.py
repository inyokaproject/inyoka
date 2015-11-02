# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import inyoka.utils.database


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
        ('portal', '0003_auto_20151029_1233'),
    ]

    operations = [
        migrations.CreateModel(
            name='Content',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('text', inyoka.utils.database.InyokaMarkupField(simplify=False, force_existing=False)),
                ('object_id', models.PositiveIntegerField()),
                ('time', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('user', models.ForeignKey(related_name='contents', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ['-time'],
                'get_latest_by': 'time',
            },
            bases=(models.Model,),
        ),
        migrations.AlterIndexTogether(
            name='content',
            index_together=set([('content_type', 'object_id')]),
        ),
    ]
