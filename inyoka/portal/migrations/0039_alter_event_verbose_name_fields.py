# Generated by Django 4.2.17 on 2024-12-26 16:30

from django.db import migrations, models

import inyoka.utils.database


class Migration(migrations.Migration):

    dependencies = [
        ("portal", "0038_alter_user_date_joined"),
    ]

    operations = [
        migrations.AlterField(
            model_name="event",
            name="date",
            field=models.DateField(db_index=True, verbose_name="Date (from)"),
        ),
        migrations.AlterField(
            model_name="event",
            name="description",
            field=inyoka.utils.database.InyokaMarkupField(
                application="ikhaya",
                blank=True,
                force_existing=False,
                simplify=False,
                verbose_name="Description",
            ),
        ),
        migrations.AlterField(
            model_name="event",
            name="enddate",
            field=models.DateField(blank=True, null=True, verbose_name="Date (to)"),
        ),
        migrations.AlterField(
            model_name="event",
            name="endtime",
            field=models.TimeField(blank=True, null=True, verbose_name="Time (to)"),
        ),
        migrations.AlterField(
            model_name="event",
            name="location",
            field=models.CharField(blank=True, max_length=128, verbose_name="Venue"),
        ),
        migrations.AlterField(
            model_name="event",
            name="location_town",
            field=models.CharField(blank=True, max_length=56, verbose_name="Town"),
        ),
        migrations.AlterField(
            model_name="event",
            name="name",
            field=models.CharField(max_length=50, verbose_name="Name"),
        ),
        migrations.AlterField(
            model_name="event",
            name="time",
            field=models.TimeField(blank=True, null=True, verbose_name="Time (from)"),
        ),
    ]
