from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ikhaya', '0007_auto_20170117_1828'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='comment',
            options={'ordering': ['id']},
        ),
    ]
