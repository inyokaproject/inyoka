from datetime import datetime, UTC

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.db import migrations


def get_models(apps):
    return apps.get_model('portal', 'User'), apps.get_model('auth', 'Group')


def create_system_groups(apps, schema_editor):
    User, Group = get_models(apps)
    db_alias = schema_editor.connection.alias
    for groupname in (settings.INYOKA_ANONYMOUS_GROUP_NAME,
                  settings.INYOKA_REGISTERED_GROUP_NAME,
                  settings.INYOKA_IKHAYA_GROUP_NAME,
                  settings.INYOKA_TEAM_GROUP_NAME):
        group, created = Group.objects.using(db_alias).get_or_create(name=groupname)
        if created:
            group.save(using=db_alias)


def create_system_users(apps, schema_editor):
    User, Group = get_models(apps)
    now = datetime.now(UTC)

    def get_or_create(username):
        try:
            return User.objects.get(username__iexact=username)
        except User.DoesNotExist:
            return User.objects.create(username=username,
                email=username.strip().lower(),
                status=0,
                date_joined=now,
                last_login=now)

    user = get_or_create(settings.ANONYMOUS_USER_NAME)
    user.status = 1
    user.password = make_password(None)
    user.save()
    group = Group.objects.get(name__iexact=settings.INYOKA_ANONYMOUS_GROUP_NAME)
    user.groups.clear()
    user.groups.add(group)
    user = get_or_create(settings.INYOKA_SYSTEM_USER)
    user.save()


class Migration(migrations.Migration):

    dependencies = [
        ('guardian', '0001_initial'),
        ('portal', '0019_remove_user_system'),
    ]

    operations = [
        migrations.RunPython(create_system_groups),
        migrations.RunPython(create_system_users),
    ]
