from django.db import migrations


def remove_sha1_password(apps, schema_editor):
    u = apps.get_model("portal", "User")

    u.objects.filter(password__startswith='sha1').update(password='was_sha1_until_2024')


class Migration(migrations.Migration):

    dependencies = [
        ("portal", "0036_user_upper_username_idx"),
    ]

    operations = [
        migrations.RunPython(remove_sha1_password),
    ]
