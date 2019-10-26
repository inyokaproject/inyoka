# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ikhaya', '0006_suggest_permissions'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='article',
            options={'ordering': ['-pub_date', '-pub_time', 'author'], 'verbose_name': 'Article', 'verbose_name_plural': 'Articles', 'permissions': (('view_unpublished_article', 'Can view unpublished articles'), ('suggest_article', 'Can suggest articles'))},
        ),
    ]
