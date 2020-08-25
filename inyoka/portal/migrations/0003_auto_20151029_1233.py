# -*- coding: utf-8 -*-


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0002_remove_userpage_content_rendered_old'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='aim',
        ),
        migrations.RemoveField(
            model_name='user',
            name='coordinates_lat',
        ),
        migrations.RemoveField(
            model_name='user',
            name='coordinates_long',
        ),
        migrations.RemoveField(
            model_name='user',
            name='icq',
        ),
        migrations.RemoveField(
            model_name='user',
            name='interests',
        ),
        migrations.RemoveField(
            model_name='user',
            name='msn',
        ),
        migrations.RemoveField(
            model_name='user',
            name='occupation',
        ),
        migrations.RemoveField(
            model_name='user',
            name='sip',
        ),
        migrations.RemoveField(
            model_name='user',
            name='skype',
        ),
        migrations.RemoveField(
            model_name='user',
            name='wengophone',
        ),
        migrations.RemoveField(
            model_name='user',
            name='yim',
        ),
    ]
