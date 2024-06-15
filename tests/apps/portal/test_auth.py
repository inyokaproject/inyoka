"""
    tests.apps.portal.test_auth
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test our custom auth backend.

    :copyright: (c) 2007-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime, timedelta, UTC

from django.conf import settings
from django.contrib.auth.models import Group
from guardian.shortcuts import assign_perm

from inyoka.portal.auth import InyokaAuthBackend
from inyoka.portal.user import User, UserBanned
from inyoka.utils.test import TestCase


class TestInyokaAuthBackend(TestCase):
    def setUp(self):
        super().setUp()
        self.backend = InyokaAuthBackend()
        self.anonymous_user = User.objects.get(username=settings.ANONYMOUS_USER_NAME)
        self.anonymous_user.set_password('inyoka')
        self.anonymous_user.save()
        anonymous_group = Group.objects.get(name=settings.INYOKA_ANONYMOUS_GROUP_NAME)
        assign_perm('portal.add_user', anonymous_group)
        self.system_user = User.objects.get(username=settings.INYOKA_SYSTEM_USER)
        self.system_user.set_password('inyoka')
        self.system_user.save()
        self.superuser = User.objects.create(username='superuser', email='superuser', is_superuser=True, status=User.STATUS_ACTIVE)
        self.superuser.save()
        self.unprivileged_user = User.objects.create(username='user', email='user@mail', status=User.STATUS_ACTIVE)
        self.unprivileged_user.set_password('inyoka')
        self.unprivileged_user.save()
        self.privileged_user = User.objects.create(username='puser', email='puser', status=User.STATUS_ACTIVE)
        self.privileged_user.set_password('inyoka')
        self.privileged_user.save()
        registered_group = Group.objects.get(name=settings.INYOKA_REGISTERED_GROUP_NAME)
        assign_perm('portal.change_user', registered_group)
        self.privileged_user.groups.add(registered_group)
        self.banned_user = User.objects.create(username='banned', email='banned', status=User.STATUS_BANNED)
        self.banned_user.set_password('inyoka')
        self.banned_user.save()
        self.banned_user.groups.add(registered_group)
        self.tbanned_user = User.objects.create(username='tbanned', email='tbanned', status=User.STATUS_BANNED)
        self.tbanned_user.set_password('inyoka')
        self.tbanned_user.banned_until = datetime.now(UTC)-timedelta(hours=1)
        self.tbanned_user.save()

    def test_login(self):
        self.assertIsInstance(self.backend.authenticate(request=None, username='user', password='inyoka'), User)
        self.assertIsNone(self.backend.authenticate(request=None))

    def test_login_by_email(self):
        self.assertIsInstance(self.backend.authenticate(request=None, username='user@mail', password='inyoka'), User)

    def test_login_banned(self):
        with self.assertRaisesMessage(UserBanned, ''):
            self.backend.authenticate(request=None, username='banned', password='inyoka')

    def test_login_temp_banned(self):
        self.assertIsInstance(self.backend.authenticate(request=None, username='tbanned', password='inyoka'), User)

    def test_login_anonymous(self):
        self.assertIsNone(self.backend.authenticate(request=None, username=settings.ANONYMOUS_USER_NAME, password='inyoka'))

    def test_login_system(self):
        self.assertIsNone(self.backend.authenticate(request=None, username=settings.INYOKA_SYSTEM_USER, password='inyoka'))

    def test_login_wrong_password(self):
        self.assertIsNone(self.backend.authenticate(request=None, username='user', password='phpbb'))

    def test_get_user_permissions(self):
        self.assertEqual(self.backend.get_user_permissions(self.unprivileged_user), set())
        self.assertEqual(self.backend.get_user_permissions(self.unprivileged_user, True), set())

    def test_get_group_permissions_by_object(self):
        self.assertEqual(self.backend.get_group_permissions(self.unprivileged_user, True), set())

    def test_get_group_permissions(self):
        excepted_permissions = {'portal.change_user'}
        self.assertEqual(self.backend.get_group_permissions(self.privileged_user), excepted_permissions)

    def test_get_all_permissions(self):
        group_permissions = self.backend.get_group_permissions(self.privileged_user)
        all_permissions = self.backend.get_all_permissions(self.privileged_user)
        self.assertEqual(group_permissions, all_permissions)

    def test_has_perm_anonymous(self):
        self.assertTrue(self.backend.has_perm(self.anonymous_user, 'portal.add_user'))
        self.assertFalse(self.backend.has_perm(self.anonymous_user, 'portal.change_user'))

    def test_has_perm_by_object(self):
        self.assertFalse(self.backend.has_perm(self.anonymous_user, 'portal.add_user', True))

    def test_has_perm(self):
        self.assertFalse(self.backend.has_perm(self.privileged_user, 'portal.add_user'))
        self.assertTrue(self.backend.has_perm(self.privileged_user, 'portal.change_user'))
        self.assertFalse(self.backend.has_perm(self.unprivileged_user, 'portal.add_user'))
        self.assertFalse(self.backend.has_perm(self.unprivileged_user, 'portal.change_user'))
        self.assertFalse(self.backend.has_perm(self.banned_user, 'portal.add_user'))

    def test_has_perm_superuser(self):
        self.assertTrue(self.backend.has_perm(self.superuser, 'portal.delete_user'))

    def test_has_module_perms_anonymous(self):
        self.assertTrue(self.backend.has_module_perms(self.anonymous_user, 'portal'))

    def test_has_module_perms(self):
        self.assertTrue(self.backend.has_module_perms(self.privileged_user, 'portal'))
        self.assertFalse(self.backend.has_module_perms(self.privileged_user, 'forum'))
        self.assertFalse(self.backend.has_module_perms(self.unprivileged_user, 'portal'))
        self.assertFalse(self.backend.has_module_perms(self.banned_user, 'portal'))

    def test_get_user(self):
        self.assertEqual(self.backend.get_user(self.privileged_user.id), self.privileged_user)
        self.assertIsNone(self.backend.get_user(65536))
