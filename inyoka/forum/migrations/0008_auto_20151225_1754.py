import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forum', '0007_auto_20151221_1103'),
    ]

    operations = [
        migrations.AlterField(
            model_name='forum',
            name='support_group',
            field=models.ForeignKey(related_name='forums', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='portal.Group', null=True),
        ),
    ]
