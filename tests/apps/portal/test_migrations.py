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
