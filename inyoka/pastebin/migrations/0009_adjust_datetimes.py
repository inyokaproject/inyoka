# Generated by Django 4.2.18 on 2025-02-23
import datetime

from django.db import migrations


def adjust_entry_datetime(apps, schema_editor):
    entry_model = apps.get_model("pastebin", "Entry")

    for e in entry_model.objects.all():
        e.pub_date = e.pub_date.astimezone().replace(tzinfo=datetime.timezone.utc)
        e.save(update_fields=["pub_date"])

class Migration(migrations.Migration):

    dependencies = [
        ("pastebin", "0008_alter_entry_pub_date"),
    ]

    operations = [
        migrations.RunPython(
            code=adjust_entry_datetime,
        ),
    ]
