# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0003_remove_text_html_render_instructions_old'),
    ]

    operations = [
        migrations.RenameField(
            model_name='page',
            old_name='last_rev',
            new_name='reviewed_version',
        ),
    ]
