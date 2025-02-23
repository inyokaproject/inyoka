# Generated by Django 4.2.18 on 2025-02-22 16:08
import datetime

from django.db import migrations


def adjust_post_datetime(apps, schema_editor):
    post_model = apps.get_model("forum", "Post")

    for p in post_model.objects.all():
        p.pub_date = p.pub_date.astimezone().replace(tzinfo=datetime.timezone.utc)
        p.save(update_fields=["pub_date"])

def adjust_poll_datetime(apps, schema_editor):
    poll_model = apps.get_model("forum", "Poll")

    for p in poll_model.objects.all():
        fields_to_update = ["start_time"]
        p.start_time = p.start_time.astimezone().replace(tzinfo=datetime.timezone.utc)

        if p.end_time:
            p.end_time = p.end_time.astimezone().replace(
                tzinfo=datetime.timezone.utc)
            fields_to_update.append("end_time")

        p.save(update_fields=fields_to_update)

def adjust_post_revision_datetime(apps, schema_editor):
    revision_model = apps.get_model("forum", "PostRevision")

    for r in revision_model.objects.all():
        r.store_date = r.store_date.astimezone().replace(tzinfo=datetime.timezone.utc)
        r.save(update_fields=["store_date"])


class Migration(migrations.Migration):

    dependencies = [
        ("forum", "0018_add_index__topic_slug"),
    ]

    operations = [
        migrations.RunPython(
            code=adjust_post_datetime,
        ),
        migrations.RunPython(
            code=adjust_poll_datetime,
        ),
        migrations.RunPython(
            code=adjust_post_revision_datetime,
        ),
    ]
