# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0017_django_permissions'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='event',
            options={'permissions': (('publish_event', 'Can publish events'), ('suggest_event', 'Can suggest events'))},
        ),
    ]
