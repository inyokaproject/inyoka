# -*- coding: utf-8 -*-


from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('pastebin', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='entry',
            name='author',
            field=models.ForeignKey(verbose_name='Author', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
    ]
