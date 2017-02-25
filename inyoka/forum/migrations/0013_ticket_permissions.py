# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forum', '0012_django_permissions'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='forum',
            options={'verbose_name': 'Forum', 'verbose_name_plural': 'Forums', 'permissions': (('delete_topic_forum', 'Can delete Topics from Forum'), ('view_forum', 'Can view Forum'), ('add_topic_forum', 'Can add Topic in Forum'), ('add_reply_forum', 'Can answer Topics in Forum'), ('sticky_forum', 'Can make Topics Sticky in Forum'), ('poll_forum', 'Can make Polls in Forum'), ('vote_forum', 'Can make Votes in Forum'), ('upload_forum', 'Can upload Attachments in Forum'), ('moderate_forum', 'Can moderate Forum'), ('manage_tickets_forum', 'Can manage tickets for Forums'))},
        ),
    ]
