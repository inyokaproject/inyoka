import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0005_auto_20151114_0130'),
        ('forum', '0005_auto_20151030_2009'),
    ]

    operations = [
        migrations.AddField(
            model_name='forum',
            name='support_group',
            field=models.ForeignKey(related_name='forums', on_delete=django.db.models.deletion.SET_NULL, to='portal.Group', null=True),
        ),
    ]
