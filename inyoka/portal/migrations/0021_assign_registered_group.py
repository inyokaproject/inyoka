# -*- coding: utf-8 -*-


from django.conf import settings
from django.db import migrations


def assign_registered_group(apps, schema_editor):
    anonymous_id = apps.get_model('portal', 'User').objects.get(username=settings.ANONYMOUS_USER_NAME).id
    registered_id = apps.get_model('auth', 'Group').objects.get(name=settings.INYOKA_REGISTERED_GROUP_NAME).id
    schema_editor.execute("INSERT INTO portal_user_groups (user_id, group_id) SELECT id, %s FROM portal_user WHERE status = 1 AND NOT id = %s;", [registered_id, anonymous_id])


class Migration(migrations.Migration):

    dependencies = [
        ('guardian', '0001_initial'),
        ('portal', '0020_system_groups_and_users'),
    ]

    operations = [
        migrations.RunPython(assign_registered_group),
    ]
