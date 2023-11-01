from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('forum', '0002_auto_20151016_1603'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='post',
            name='rendered_text_old',
        ),
    ]
