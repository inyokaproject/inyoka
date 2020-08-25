# -*- coding: utf-8 -*-


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pastebin', '0002_entry_author'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='entry',
            name='rendered_code_old',
        ),
    ]
