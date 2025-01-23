"""
    tests.apps.portal.test_migrations
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test portal migrations.

    :copyright: (c) 2023-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from datetime import date, datetime, time, timezone

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


class TestEventDateTimeMerge(MigratorTestCase):
    migrate_from = ("portal", "0039_alter_event_verbose_name_fields")
    migrate_to = ("portal", "0040_event__datetimes__helptext_visible")

    def prepare(self):
        """Prepare some data before the migration."""
        User = self.old_state.apps.get_model("portal", "User")
        self.author = User.objects.create(
            username="foo", email="foo@local.localhost",
        )

        event_model = self.old_state.apps.get_model("portal", "Event")
        only_start_date = event_model.objects.create(name="foo", slug="foo",
                                                     date=date(2000, 1, 1),
                                                     author=self.author)
        self.only_start_date_slug = only_start_date.slug

        only_start_date_and_time = event_model(name="foobar", slug="foobar",
                                               date=date(2001, 1, 1),
                                               time=time(1, 11), author=self.author)
        only_start_date_and_time.save()
        self.only_start_date_and_time_slug = only_start_date_and_time.slug

        only_end_date = event_model(name="foo2", slug="foo2", date=date(2001, 1, 1),
                                    time=time(1, 11),
                                    enddate=date(2001, 1, 2),
                                    author=self.author)
        only_end_date.save()
        self.only_end_date_slug = only_end_date.slug

        end_date_and_time = event_model(name="foo3", slug="foo3", date=date(2001, 1, 1),
                                        time=time(1, 11),
                                        enddate=date(2001, 1, 2),
                                        endtime=time(1, 12),
                                        author=self.author)
        end_date_and_time.save()
        self.end_date_and_time_slug = end_date_and_time.slug


    def test_only_start_date(self):
        event_model = self.new_state.apps.get_model("portal", "Event")

        e = event_model.objects.get(slug=self.only_start_date_slug)
        self.assertEqual(e.start, datetime(2000, 1, 1, 0, 0, tzinfo=timezone.utc))
        self.assertEqual(e.end, datetime(2000, 1, 1, 21, 59, tzinfo=timezone.utc))

    def test_only_start_date_and_time(self):
        event_model = self.new_state.apps.get_model("portal", "Event")

        e = event_model.objects.get(slug=self.only_start_date_and_time_slug)
        self.assertEqual(e.start, datetime(2001, 1, 1, 1, 11, tzinfo=timezone.utc))
        self.assertEqual(e.end, datetime(2001, 1, 1, 21, 59, tzinfo=timezone.utc))

    def test_only_end_date(self):
        event_model = self.new_state.apps.get_model("portal", "Event")

        e = event_model.objects.get(slug=self.only_end_date_slug)
        self.assertEqual(e.start, datetime(2001, 1, 1, 1, 11, tzinfo=timezone.utc))
        self.assertEqual(e.end, datetime(2001, 1, 2, 21, 59, tzinfo=timezone.utc))

    def test_end_date_and_time(self):
        event_model = self.new_state.apps.get_model("portal", "Event")

        e = event_model.objects.get(slug=self.end_date_and_time_slug)
        self.assertEqual(e.start, datetime(2001, 1, 1, 1, 11, tzinfo=timezone.utc))
        self.assertEqual(e.end, datetime(2001, 1, 2, 1, 12, tzinfo=timezone.utc))
