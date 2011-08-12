from optparse import make_option
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create a user with all priviliges"

    option_list = BaseCommand.option_list + (
        make_option('-u', '--username', action='store',
                    default=None, dest='username'),
        make_option('-e', '--email', action='store',
                    default=None, dest='email'),
        make_option('-p', '--password', action='store',
                    default=None, dest='password')
    )

    def handle(self, *args, **options):
        from getpass import getpass
        username = options['username']
        email = options['email']
        password = options['password']
        while not username:
            username = raw_input('username: ')
        while not email:
            email = raw_input('email: ')
        if not password:
            while not password:
                password = getpass('password: ')
                if password:
                    if password == getpass('repeat: '):
                        break
                    password = ''
        from inyoka.portal.user import User, PERMISSION_NAMES
        from inyoka.forum.models import Forum, Privilege
        from inyoka.forum.acl import PRIVILEGES_DETAILS, join_flags
        user = User.objects.register_user(username, email, password, False)
        permissions = 0
        for perm in PERMISSION_NAMES.keys():
            permissions |= perm
        user._permissions = permissions
        user.save()
        bits = dict(PRIVILEGES_DETAILS).keys()
        bits = join_flags(*bits)
        for forum in Forum.objects.all():
            privilege = Privilege(
                user=user,
                forum=forum,
                positive=bits,
                negative=0).save()
        print 'created superuser'
