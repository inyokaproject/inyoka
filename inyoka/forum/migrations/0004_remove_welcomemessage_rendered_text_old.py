# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('forum', '0003_remove_post_rendered_text_old'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='welcomemessage',
            name='rendered_text_old',
        ),
    ]
