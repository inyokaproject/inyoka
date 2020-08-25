# -*- coding: utf-8 -*-


from django.conf import settings
from django.db import migrations, models

import inyoka.utils.database


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('forum', '0006_forum_support_group'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='forum',
            name='welcome_message',
        ),
        migrations.AddField(
            model_name='forum',
            name='welcome_read_users',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='forum',
            name='welcome_text',
            field=inyoka.utils.database.InyokaMarkupField(simplify=False, null=True, force_existing=False),
        ),
        migrations.AddField(
            model_name='forum',
            name='welcome_title',
            field=models.CharField(max_length=120, null=True),
        ),
        migrations.AlterField(
            model_name='forum',
            name='slug',
            field=models.SlugField(unique=True, max_length=100),
        ),
        migrations.DeleteModel(
            name='WelcomeMessage',
        ),
    ]
