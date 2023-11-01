from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0013_copy_user_group_m2m'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='groups_old',
        ),
        migrations.DeleteModel(
            name='Group',
        ),
    ]
