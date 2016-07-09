# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ikhaya', '0005_django_permissions'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='article',
            options={'ordering': ['-pub_date', '-pub_time', 'author'], 'verbose_name': 'Article', 'verbose_name_plural': 'Articles', 'permissions': (('publish_article', 'User can publish articles'), ('view_article', 'User can view published articles'), ('view_unpublished_article', 'User can view unpublished articles'), ('suggest_article', 'User can suggest articles'))},
        ),
    ]
