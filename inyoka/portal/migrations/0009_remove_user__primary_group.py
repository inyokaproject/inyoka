# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0008_user_icon'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='_primary_group',
        ),
    ]
