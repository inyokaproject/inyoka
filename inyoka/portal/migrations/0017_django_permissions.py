# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0016_django_guardian_mixins'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='event',
            options={'permissions': (('publish_event', 'Can publish events'),)},
        ),
        migrations.AlterModelOptions(
            name='privatemessage',
            options={'ordering': ('-pub_date',), 'permissions': (('send_group_privatemessage', 'Can send Group Private Messages'),)},
        ),
        migrations.AlterModelOptions(
            name='user',
            options={'permissions': (('subscribe_user', 'Can subscribe Users'),)},
        ),
    ]
