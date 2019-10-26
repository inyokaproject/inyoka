# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ikhaya', '0004_auto_20160226_2043'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='article',
            options={'ordering': ['-pub_date', '-pub_time', 'author'], 'verbose_name': 'Article', 'verbose_name_plural': 'Articles', 'permissions': (('publish_article', 'Can publish articles'), ('view_article', 'Can view published articles'), ('view_unpublished_article', 'Can view unpublished articles'))},
        ),
    ]
