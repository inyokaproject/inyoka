from django_test_migrations.contrib.unittest_case import MigratorTestCase


class TestUserJabberFieldMigration(MigratorTestCase):
    migrate_from = ("portal", "0033_auto_20230312_1704")
    migrate_to = ("portal", "0034_alter_user_jabber")

    def prepare(self):
        """Prepare some data before the migration."""
        User = self.old_state.apps.get_model("portal", "User")
        User.objects.create(
            username="foo", email="foo@local.localhost", jabber="foo@local.localhost"
        )

    def test_jabber_still_available(self):
        User = self.new_state.apps.get_model("portal", "User")
        u = User.objects.get(username="foo")
        self.assertEqual(u.jabber, "foo@local.localhost")


class TestUserJabberContentMigration(MigratorTestCase):
    migrate_from = ("portal", "0034_alter_user_jabber")
    migrate_to = ("portal", "0035_auto_20231127_0114")

    def prepare(self):
        """Prepare some data before the migration."""
        User = self.old_state.apps.get_model("portal", "User")
        User.objects.create(
            username="foo", email="foo@local.localhost", jabber="foo@local.localhost"
        )

        u = User.objects.create(
            username="foo2", email="foo2@local.localhost", jabber="foo2@local.localhost"
        )
        u.settings["notify"] = ["jabber"]
        u.settings["show_jabber"] = True
        u.save()
        self.assertTrue("show_jabber" in u.settings.keys())
        self.assertEqual(u.settings["notify"], ["jabber"])

    def test_jabber_id_removed(self):
        User = self.new_state.apps.get_model("portal", "User")
        u = User.objects.get(username="foo")
        self.assertEqual(u.jabber, "")

    def test_public_jabber_id_left(self):
        User = self.new_state.apps.get_model("portal", "User")
        u = User.objects.get(username="foo2")
        self.assertEqual(u.jabber, "foo2@local.localhost")
        self.assertFalse("show_jabber" in u.settings.keys())
        self.assertEqual(u.settings["notify"], [])


class TestUserSha1PasswordRemoval(MigratorTestCase):
    migrate_from = ("portal", "0036_user_upper_username_idx")
    migrate_to = ("portal", "0037_remove_sha1_user")

    def prepare(self):
        """Prepare some data before the migration."""
        User = self.old_state.apps.get_model("portal", "User")

        User.objects.create(
            username="foo", email="foo@local.localhost",
            password="sha1$ZmJGfGJI50k1pEFjgSClAd$e79d4abf01376803ef33579c1ba215f71dace012"
        )
        User.objects.create(
            username="foo2", email="foo2@local.localhost",
            password="sha1$not_valid"
        )

        User.objects.create(
            username="test", email="test@local.localhost", password="argon2$argon2id$v=19$m=102400,t=2,p=invalid"
        )
        User.objects.create(
            username="test2", email="test2@local.localhost", password="pbkdf2_sha256$600000$not_valid"
        )

    def test_sha1_password_replaced(self):
        User = self.new_state.apps.get_model("portal", "User")

        u = User.objects.get(username="foo")
        self.assertEqual(u.password, "was_sha1_until_2024")

        u = User.objects.get(username="foo2")
        self.assertEqual(u.password, "was_sha1_until_2024")

    def test_other_passwords_untouched(self):
        User = self.new_state.apps.get_model("portal", "User")

        u = User.objects.get(username="test")
        self.assertEqual(u.password, "argon2$argon2id$v=19$m=102400,t=2,p=invalid")

        u = User.objects.get(username="test2")
        self.assertEqual(u.password, "pbkdf2_sha256$600000$not_valid")
