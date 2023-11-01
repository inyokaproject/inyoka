from django.db import migrations, models


def copy_user_icon(apps, schema_editor):
    User = apps.get_model('portal','User')
    db_alias = schema_editor.connection.alias
    for user in User.objects.using(db_alias).exclude(_primary_group__isnull=True).all():
        user.icon = user._primary_group.icon
        user.save()

class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0007_auto_20160522_1226'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='icon',
            field=models.ImageField(upload_to='portal/team_icons', null=True, verbose_name='Team icon', blank=True),
        ),
        migrations.RunPython(copy_user_icon, migrations.RunPython.noop),
    ]
