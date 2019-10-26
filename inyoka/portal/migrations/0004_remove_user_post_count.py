# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0003_auto_20151029_1233'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='post_count',
        ),
    ]
