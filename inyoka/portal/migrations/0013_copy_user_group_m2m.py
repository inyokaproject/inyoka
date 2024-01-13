from django.db import migrations, models


def copy_user_group_relations(apps, schema_editor):
    User = apps.get_model('portal', 'User')
    Group = apps.get_model('auth', 'Group')
    db_alias = schema_editor.connection.alias
    for relation in User.groups_old.through.objects.using(db_alias).all():
        user = User.objects.using(db_alias).get(id=relation.user_id)
        group = Group.objects.using(db_alias).get(id=relation.group_id)
        user.groups.add(group)


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
        ('portal', '0012_auto_20160702_1824'),
    ]

    operations = [
        migrations.RunPython(copy_user_group_relations, migrations.RunPython.noop),
    ]
