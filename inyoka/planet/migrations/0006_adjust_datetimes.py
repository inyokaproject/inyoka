# Generated by Django 4.2.18 on 2025-02-23 20:49
import datetime

from django.db import migrations


def adjust_blog_last_sync(apps, schema_editor):
    blog_model = apps.get_model("planet", "Blog")

    for b in blog_model.objects.all():
        if not b.last_sync:
            continue
        b.last_sync = b.last_sync.astimezone().replace(tzinfo=datetime.timezone.utc)
        b.save(update_fields=["last_sync"])

def adjust_blog_entry_datetime(apps, schema_editor):
    entry_model = apps.get_model("planet", "Entry")

    for e in entry_model.objects.all():
        e.pub_date = e.pub_date.astimezone().replace(tzinfo=datetime.timezone.utc)
        e.updated = e.updated.astimezone().replace(tzinfo=datetime.timezone.utc)
        e.save(update_fields=["pub_date", "updated"])

class Migration(migrations.Migration):

    dependencies = [
        ("planet", "0005_auto_20191027_1814"),
    ]

    operations = [
        migrations.RunPython(
            code=adjust_blog_last_sync,
        ),
        migrations.RunPython(
            code=adjust_blog_entry_datetime,
        ),
    ]
