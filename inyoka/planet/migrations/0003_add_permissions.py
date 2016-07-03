# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('planet', '0002_auto_20151016_1603'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='blog',
            options={'ordering': ('name',), 'verbose_name': 'Blog', 'verbose_name_plural': 'Blogs', 'permissions': (('view_blog', 'View Blogs'), ('suggest_blog', 'Suggest Blogs'))},
        ),
        migrations.AlterModelOptions(
            name='entry',
            options={'ordering': ('-pub_date',), 'get_latest_by': 'pub_date', 'verbose_name': 'Entry', 'verbose_name_plural': 'Entries', 'permissions': (('hide_entry', 'Hide Entry'),)},
        ),
    ]
