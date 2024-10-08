# Generated by Django 1.11.25 on 2019-10-27 18:14

import os

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0026_remove_user_forum_last_read'),
    ]

    operations = [
        migrations.AlterField(
            model_name='privatemessageentry',
            name='folder',
            field=models.SmallIntegerField(choices=[(0, 'sent'), (1, 'inbox'), (2, 'trash'), (3, 'archive')], null=True, verbose_name='Folder'),
        ),
        migrations.AlterField(
            model_name='staticfile',
            name='file',
            field=models.FileField(upload_to='portal/files', verbose_name='File'),
        ),
        migrations.AlterField(
            model_name='user',
            name='icon',
            field=models.FilePathField(blank=True, match='.*\\.png', null=True, path=os.path.join(settings.MEDIA_ROOT, 'portal/team_icons'), verbose_name='Group icon'),
        ),
    ]
