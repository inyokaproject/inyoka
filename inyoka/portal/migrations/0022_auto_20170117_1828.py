# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0021_assign_registered_group'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='event',
            options={'permissions': (('suggest_event', 'Can suggest events'),)},
        ),
    ]
