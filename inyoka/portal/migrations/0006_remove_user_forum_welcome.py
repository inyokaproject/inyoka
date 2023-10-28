from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0005_auto_20151114_0130'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='forum_welcome',
        ),
    ]
