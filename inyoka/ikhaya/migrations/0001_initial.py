# -*- coding: utf-8 -*-


import datetime

from django.db import migrations, models

import inyoka.utils.database


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Article',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('pub_date', models.DateField(verbose_name='Date', db_index=True)),
                ('pub_time', models.TimeField(verbose_name='Time')),
                ('updated', models.DateTimeField(db_index=True, null=True, verbose_name='Last change', blank=True)),
                ('subject', models.CharField(max_length=180, verbose_name='Headline')),
                ('intro', inyoka.utils.database.InyokaMarkupField(simplify=False, verbose_name='Introduction', force_existing=False)),
                ('text', inyoka.utils.database.InyokaMarkupField(simplify=False, verbose_name='Text', force_existing=False)),
                ('public', models.BooleanField(default=False, verbose_name='Public')),
                ('slug', models.SlugField(max_length=100, verbose_name='Slug', blank=True)),
                ('is_xhtml', models.BooleanField(default=False, verbose_name='XHTML Markup')),
                ('comment_count', models.IntegerField(default=0)),
                ('comments_enabled', models.BooleanField(default=True, verbose_name='Allow comments')),
            ],
            options={
                'ordering': ['-pub_date', '-pub_time', 'author'],
                'verbose_name': 'Article',
                'verbose_name_plural': 'Articles',
            },
            bases=(models.Model, inyoka.utils.database.LockableObject),
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=180)),
                ('slug', models.CharField(db_index=True, unique=True, max_length=100, verbose_name='Slug', blank=True)),
            ],
            options={
                'ordering': ('name',),
                'verbose_name': 'Category',
                'verbose_name_plural': 'Categories',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('text', inyoka.utils.database.InyokaMarkupField(simplify=False, force_existing=False)),
                ('pub_date', models.DateTimeField()),
                ('deleted', models.BooleanField(default=False)),
                ('rendered_text_old', models.TextField(db_column='rendered_text')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('text', inyoka.utils.database.InyokaMarkupField(simplify=False, force_existing=False)),
                ('pub_date', models.DateTimeField()),
                ('deleted', models.BooleanField(default=False)),
                ('solved', models.BooleanField(default=False)),
                ('rendered_text_old', models.TextField(db_column='rendered_text')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Suggestion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('pub_date', models.DateTimeField(default=datetime.datetime.utcnow, verbose_name='Datum')),
                ('title', models.CharField(max_length=100, verbose_name='Title')),
                ('text', inyoka.utils.database.InyokaMarkupField(simplify=False, verbose_name='Text', force_existing=False)),
                ('intro', inyoka.utils.database.InyokaMarkupField(simplify=False, verbose_name='Introduction', force_existing=False)),
                ('notes', inyoka.utils.database.InyokaMarkupField(default='', simplify=False, verbose_name='Annotations to the team', force_existing=False, blank=True)),
            ],
            options={
                'verbose_name': 'Article suggestion',
                'verbose_name_plural': 'Article suggestions',
            },
            bases=(models.Model,),
        ),
    ]
