# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
        ('portal', '0011_auto_20160702_1816'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='groups',
            field=models.ManyToManyField(related_name='user_set', verbose_name='Groups', to='auth.Group', blank=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='groups_old',
            field=models.ManyToManyField(related_name='user_set_old', verbose_name='Groups', to='portal.Group', blank=True),
        ),
    ]
