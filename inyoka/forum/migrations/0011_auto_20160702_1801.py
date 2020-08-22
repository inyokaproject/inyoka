# -*- coding: utf-8 -*-


from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('forum', '0010_auto_20160106_1247'),
    ]

    operations = [
        migrations.AlterField(
            model_name='forum',
            name='support_group',
            field=models.ForeignKey(related_name='forums', on_delete=django.db.models.deletion.SET_NULL, verbose_name='Support group', blank=True, to='auth.Group', null=True),
        ),
        migrations.AlterField(
            model_name='privilege',
            name='group',
            field=models.ForeignKey(to='auth.Group', null=True, on_delete=models.CASCADE),
        ),
    ]
