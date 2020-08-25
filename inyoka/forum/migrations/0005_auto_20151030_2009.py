# -*- coding: utf-8 -*-


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('forum', '0004_remove_welcomemessage_rendered_text_old'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='forum',
            name='post_count',
        ),
        migrations.RemoveField(
            model_name='forum',
            name='topic_count',
        ),
        migrations.RemoveField(
            model_name='topic',
            name='post_count',
        ),
    ]
