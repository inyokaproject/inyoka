from django.db import migrations, models

def postgresql_drop_indexes(apps, schema_editor):
    if schema_editor.connection.vendor.startswith('postgre'):
        schema_editor.execute('DROP INDEX IF EXISTS portal_user_groups_e8701ad4;')
        schema_editor.execute('DROP INDEX IF EXISTS portal_user_groups_0e939a4f;')
        schema_editor.execute('ALTER TABLE portal_user_groups_old DROP CONSTRAINT IF EXISTS portal_user_groups_user_id_group_id_bad90d85_uniq;')
        schema_editor.execute('DROP INDEX IF EXISTS portal_user_groups_user_id_group_id_bad90d85_uniq;')
        schema_editor.execute('DROP INDEX IF EXISTS portal_user_groups_user_id_120e8705;')
        schema_editor.execute('DROP INDEX IF EXISTS portal_user_groups_group_id_39d85d73;')

class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0010_copy_groups'),
    ]

    operations = [
        migrations.RenameField(
            model_name='user',
            old_name='groups',
            new_name='groups_old',
        ),
        migrations.RunPython(postgresql_drop_indexes),
    ]
