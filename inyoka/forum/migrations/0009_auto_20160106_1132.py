# -*- coding: utf-8 -*-


import django.db.models.deletion
from django.db import migrations, models

import inyoka.utils.database


class Migration(migrations.Migration):

    dependencies = [
        ('forum', '0008_auto_20151225_1754'),
    ]

    operations = [
        migrations.AlterField(
            model_name='forum',
            name='parent',
            field=models.ForeignKey(related_name='_children', on_delete=django.db.models.deletion.PROTECT, blank=True, to='forum.Forum', null=True),
        ),
        migrations.AlterField(
            model_name='forum',
            name='welcome_text',
            field=inyoka.utils.database.InyokaMarkupField(simplify=False, null=True, force_existing=False, blank=True),
        ),
        migrations.AlterField(
            model_name='forum',
            name='welcome_title',
            field=models.CharField(max_length=120, null=True, blank=True),
        ),
    ]
