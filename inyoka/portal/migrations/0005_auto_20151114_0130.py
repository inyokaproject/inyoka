# -*- coding: utf-8 -*-


from django.db import migrations, models

import inyoka.portal.models


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0004_remove_user_post_count'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='subscription',
            managers=[
                ('objects', inyoka.portal.models.SubscriptionManager()),
            ],
        ),
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(unique=True, max_length=254, verbose_name='Email address', db_index=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='last_login',
            field=models.DateTimeField(null=True, verbose_name='last login', blank=True),
        ),
    ]
