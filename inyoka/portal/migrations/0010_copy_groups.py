from django.db import migrations, models
import django

def copy_groups(apps, schema_editor):
    InyokaGroup = apps.get_model('portal','Group')
    AuthGroup = apps.get_model('auth','Group')
    db_alias = schema_editor.connection.alias
    inyoka_groups = InyokaGroup.objects.using(db_alias).values_list('id','name')
    for group_id, group_name in inyoka_groups:
        AuthGroup.objects.using(db_alias).create(id=group_id, name=group_name)

class Migration(migrations.Migration):

    dependencies = [
        ('forum', '0010_auto_20160106_1247'),
        ('auth', '0006_require_contenttypes_0002'),
        ('portal', '0009_remove_user__primary_group'),
    ]

    operations = [
        migrations.RunPython(copy_groups, migrations.RunPython.noop),
    ]
