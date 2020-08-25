# -*- coding: utf-8 -*-


import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import inyoka.utils.database


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('forum', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('file', models.FileField(upload_to='wiki/attachments/%S/%W')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MetaData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('key', models.CharField(max_length=30, db_index=True)),
                ('value', models.CharField(max_length=255, db_index=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Page',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=200, db_index=True)),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': 'Wiki page',
                'verbose_name_plural': 'Wiki pages',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Revision',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('change_date', models.DateTimeField(db_index=True)),
                ('note', models.CharField(max_length=512)),
                ('deleted', models.BooleanField(default=False)),
                ('remote_addr', models.CharField(max_length=200, null=True)),
                ('attachment', models.ForeignKey(blank=True, to='wiki.Attachment', null=True, on_delete=models.CASCADE)),
                ('page', models.ForeignKey(related_name='revisions', to='wiki.Page', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['-change_date'],
                'get_latest_by': 'change_date',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Text',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value', inyoka.utils.database.InyokaMarkupField(simplify=False, force_existing=False)),
                ('hash', models.CharField(unique=True, max_length=40, db_index=True)),
                ('html_render_instructions_old', models.TextField(null=True, db_column='html_render_instructions')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='revision',
            name='text',
            field=models.ForeignKey(related_name='revisions', to='wiki.Text', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='revision',
            name='user',
            field=models.ForeignKey(related_name='wiki_revisions', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='page',
            name='last_rev',
            field=models.ForeignKey(related_name='+', to='wiki.Revision', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='page',
            name='topic',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='forum.Topic', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='metadata',
            name='page',
            field=models.ForeignKey(to='wiki.Page', on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
