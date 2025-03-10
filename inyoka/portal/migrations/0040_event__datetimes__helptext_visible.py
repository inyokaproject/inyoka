# Generated by Django 4.2.17 on 2025-01-13

import datetime

from django.db import migrations, models


def migrate_start_and_end_dates_to_datetime_field(apps, schema_editor):
    event_model = apps.get_model("portal", "Event")

    for e in event_model.objects.all():
        # if no time is in the database, it's a whole day event. So we assume it starts at 00:00 UTC
        start_time = e.time or datetime.time(0, 0)
        start_datetime = datetime.datetime.combine(e.date, start_time, datetime.timezone.utc)
        e.start = start_datetime

        # if no end date is in the database, we assume it ends at the same day as it starts
        end_date = e.enddate or e.date
        # if no end time is in the database, we assume it ends in the late evening
        # (to keep things simple 21:59 UTC, which is e.g. 23:59 CEST or 22:59 CET)
        end_time = e.endtime or datetime.time(21, 59)
        e.end = datetime.datetime.combine(end_date, end_time, datetime.timezone.utc)

        e.save()


class Migration(migrations.Migration):

    dependencies = [
        ("portal", "0039_alter_event_verbose_name_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="end",
            field=models.DateTimeField(
                default=datetime.datetime(
                    2000, 1, 1, 0, 0, 1, tzinfo=datetime.timezone.utc
                ),
                verbose_name="End date",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="event",
            name="start",
            field=models.DateTimeField(
                db_index=True,
                default=datetime.datetime(
                    2000, 1, 1, 0, 0, 2, tzinfo=datetime.timezone.utc
                ),
                verbose_name="Start date",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="event",
            name="visible",
            field=models.BooleanField(default=False, verbose_name="Display event?"),
        ),
        migrations.RunPython(
            code=migrate_start_and_end_dates_to_datetime_field,
        ),
        migrations.RemoveField(
            model_name="event",
            name="date",
        ),
        migrations.RemoveField(
            model_name="event",
            name="enddate",
        ),
        migrations.RemoveField(
            model_name="event",
            name="endtime",
        ),
        migrations.RemoveField(
            model_name="event",
            name="time",
        ),
    ]
