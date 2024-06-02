"""
    tests.apps.portal.test_admin
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test some admin commands

    :copyright: (c) 2007-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import io

from django.conf import settings
from django.contrib.auth.hashers import SHA1PasswordHasher
from django.core import mail, management
from django.utils import translation

from inyoka.portal.user import User
from inyoka.utils.test import TestCase, InyokaClient


class TestAdminCommands(TestCase):

    def test_rename_users(self):
        User.objects.register_user("gandalf", "gandalf@hdr.de", "pwd", False)
        User.objects.register_user("saroman", "saroman@hdr.de", "pwd", False)
        rename_file = io.StringIO('[{"oldname":"gandalf", "newname":"thewhite"},{"oldname":"saroman", "newname":"thedead"}]')
        management.call_command("renameusers", file=rename_file, verbosity=0)
        self.assertEqual(str(User.objects.get_by_username_or_email("gandalf@hdr.de")), "thewhite")
        self.assertEqual(str(User.objects.get_by_username_or_email("saroman@hdr.de")), "thedead")
        self.assertFalse('thewhite' in mail.outbox[1].body)
        self.assertTrue('thedead' in mail.outbox[1].body)


class TestAdminCommandUpgradePassword(TestCase):

    client_class = InyokaClient

    def setUp(self):
        User.objects.create(
            username="foo", email="foo@local.localhost",
            # plaintext password: 'test'
            password="sha1$ZmJGfGJI50k1pEFjgSClAd$e79d4abf01376803ef33579c1ba215f71dace012"
        )

    def test_upgrade_passwords_offline(self):
        management.call_command('upgrade_passwords_offline', verbosity=0)

        self.assertEqual(User.objects.filter(password__startswith="sha1").count(), 0)
        self.assertEqual(User.objects.filter(password__startswith="argon2_wrapped_sha1").count(), 1)

    def test_password(self):
        management.call_command('upgrade_passwords_offline', verbosity=0)

        u = User.objects.get(username='foo')
        print(u.password)

        self.assertTrue(u.has_usable_password())
        self.assertTrue(u.check_password('test'))

        u.refresh_from_db()
        self.assertTrue(u.password.starswith('argon2$'))

    def test_login_after_upgrade(self):
        management.call_command('upgrade_passwords_offline', verbosity=0)

        postdata = {'username': 'foo', 'password': 'test'}
        with translation.override('en-us'):
            response = self.client.post('/login/', postdata, follow=True)

            print(response.content.decode())

            self.assertRedirects(response, 'http://' + settings.BASE_DOMAIN_NAME + '/')
            self.assertInHTML('<div class="message success">%s</div>' % _('You have successfully logged in.'),
                              response.content.decode(), count=1)

        self.assertEqual(User.objects.filter(password__startswith="argon2_wrapped_sha1").count(), 0)
        self.assertEqual(User.objects.filter(password__startswith="argon2$").count(), 1)
