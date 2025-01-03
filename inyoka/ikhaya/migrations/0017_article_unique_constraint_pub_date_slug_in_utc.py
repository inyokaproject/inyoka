# Generated by Django 4.2.17 on 2025-01-03 23:09

from django.db import migrations, models

import inyoka.utils.database


class Migration(migrations.Migration):

    dependencies = [
        ("ikhaya", "0016_unify_article_updated_semantic"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="article",
            name="unique_pub_date_slug",
        ),
        migrations.AddConstraint(
            model_name="article",
            constraint=models.UniqueConstraint(
                inyoka.utils.database.TruncDateUtc("publication_datetime"),
                models.F("slug"),
                name="unique_pub_date_slug",
            ),
        ),
    ]
