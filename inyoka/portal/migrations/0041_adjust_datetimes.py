# Generated by Django 4.2.18 on 2025-02-23 20:47

import datetime

from django.db import migrations


def adjust_private_message_datetime(apps, schema_editor):
    pm_model = apps.get_model("portal", "PrivateMessage")

    for pm in pm_model.objects.all():
        pm.pub_date = pm.pub_date.astimezone().replace(tzinfo=datetime.timezone.utc)
        pm.save(update_fields=["pub_date"])

def adjust_user_datetimes(apps, schema_editor):
    user_model = apps.get_model("portal", "User")

    for u in user_model.objects.all():
        u.date_joined = u.date_joined.astimezone().replace(tzinfo=datetime.timezone.utc)
        u.save(update_fields=["date_joined"])


class Migration(migrations.Migration):

    dependencies = [
        ("portal", "0040_event__datetimes__helptext_visible"),
    ]

    operations = [
        migrations.RunPython(
            code=adjust_private_message_datetime,
        ),
        migrations.RunPython(
            code=adjust_user_datetimes,
        ),
    ]
