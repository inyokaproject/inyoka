# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0023_auto_20170226_0018'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='gpgkey',
            field=models.CharField(max_length=255, verbose_name='GPG fingerprint', blank=True),
        ),
    ]
