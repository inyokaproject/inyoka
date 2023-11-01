from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0006_remove_user_forum_welcome'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='system',
            field=models.BooleanField(default=False, verbose_name='System group'),
        ),
        migrations.AddField(
            model_name='user',
            name='system',
            field=models.BooleanField(default=False, verbose_name='System user'),
        ),
    ]
