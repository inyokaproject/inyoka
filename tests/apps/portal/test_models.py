"""
    tests.apps.portal.test_models
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test portal models.

    :copyright: (c) 2012-2026 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import csv
import gzip
import io
import zipfile
from datetime import timedelta
from logging import DEBUG
from os import path

import responses
from django.conf import settings
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone as dj_timezone
from freezegun import freeze_time

from inyoka.portal.models import (
    PRIVMSG_FOLDERS,
    Linkmap,
    PrivateMessage,
    PrivateMessageEntry,
    SpamEmailAddress,
)
from inyoka.portal.user import User
from inyoka.utils.test import TestCase
from inyoka.utils.urls import href


class TestLinkmapModel(TestCase):

    error_message_token = 'Only lowercase letters, - and _ allowed. Numbers as postfix.'

    def token(self, token):
        Linkmap(token=token, url='http://example.test').full_clean()

    def test_valid_token(self):
        self.token('debian_de')
        self.token('kubuntu-de')
        self.token('canonicalsubdomain')
        self.token('sourceforge2')

    def test_invalid_token__umlaut(self):
        with self.assertRaisesMessage(ValidationError, self.error_message_token):
            self.token('öäüß')

        with self.assertRaisesMessage(ValidationError, self.error_message_token):
            self.token('jkoijoijö')

    def test_invalid_token__uppercase(self):
        with self.assertRaisesMessage(ValidationError, self.error_message_token):
            self.token('Adfv')

        with self.assertRaisesMessage(ValidationError, self.error_message_token):
            self.token('dfvD')

    def url(self, url):
        Linkmap(token='example', url=url).full_clean()

    def test_valid_url(self):
        self.url('http://example.test')
        self.url('https://startpage.test/do/search?cat=web&language=deutsch&query=PAGE&ff=')
        self.url('https://PAGE.wordpress.test/')
        self.url('https://web.archive.test/web/*/https://')

    def test_invalid_url(self):
        with self.assertRaisesMessage(ValidationError, 'Enter a valid URL.'):
            self.url('foo.test')

        with self.assertRaisesMessage(ValidationError, 'Enter a valid URL.'):
            self.url('apt:')

        with self.assertRaisesMessage(ValidationError, 'Enter a valid URL.'):
            self.url('apt://')

        with self.assertRaisesMessage(ValidationError, 'Enter a valid URL.'):
            self.url('https://PAGE')

    def test_uniqueness_token(self):
        token = 'example'
        Linkmap.objects.create(token=token, url='http://example.test')

        with self.assertRaises(IntegrityError):
            Linkmap.objects.create(token=token, url='http://example2.test')


class TestLinkmapManager(TestCase):

    def setUp(self):
        super().setUp()

        Linkmap.objects.create(token='example', url='http://example.test', icon='example.png')

        self.css_file = Linkmap.objects.generate_css()
        self.full_path = path.join(settings.MEDIA_ROOT, 'linkmap', self.css_file)

    def test_generate_css__created_css(self):
        self.assertIsNotNone(self.css_file)

        with open(self.full_path) as f:
            css = ('/* linkmap for inter wiki links \n :license: BSD*/a.interwiki { padding-left: 20px; }'
                   'a.interwiki-example { background-image: url("%s"); }')
            self.assertEqual(f.read(), css % href('media', 'example.png'))

    def test_generate_css__generates_gzip_file(self):
        with open(self.full_path) as f, gzip.open(self.full_path + '.gz', 'rt') as gzip_f:
            self.assertEqual(gzip_f.read(), f.read())

    def test_generate_css__deletes_old_files(self):
        self.assertTrue(path.exists(self.full_path))

        Linkmap.objects.create(token='example2', url='http://example.test', icon='example2.png')
        self.css_file = Linkmap.objects.generate_css()

        self.assertFalse(path.exists(self.full_path))
        self.assertTrue(path.exists(path.join(settings.MEDIA_ROOT, 'linkmap', self.css_file)))


class TestPrivateMessageManager(TestCase):

    def setUp(self):
        super().setUp()

        user = User.objects.register_user('testing', 'example@example.com',
                                               'pwd', False)
        self.other_user = User.objects.register_user(
            'other_user',
            'example2@example.com',
            'pwd', False)

        pm = PrivateMessage(author=user, subject="message", pub_date=dj_timezone.now())
        pm.send([self.other_user])

    def test_orphan_messages__no_orphans(self):
        self.assertEqual(PrivateMessage.objects.count(), 1)
        self.assertEqual(PrivateMessageEntry.objects.count(), 2)

        self.assertEqual(list(PrivateMessage.objects.orphan_messages()), [])

    def test_orphan_messages__only_orphans(self):
        self.assertEqual(PrivateMessage.objects.count(), 1)
        self.assertEqual(PrivateMessageEntry.objects.count(), 2)

        PrivateMessageEntry.objects.all().delete()

        self.assertEqual(PrivateMessage.objects.count(), 1)
        self.assertEqual(PrivateMessageEntry.objects.count(), 0)

        self.assertEqual(list(PrivateMessage.objects.orphan_messages()), [PrivateMessage.objects.get()])

    def test_orphan_messages__mixture_orphans_and_no_orphans(self):
        self.third_user = User.objects.register_user(
            'third_user',
            'example3@inyoka.test',
            'pwd',
            False
        )

        pm2 = PrivateMessage(author=self.other_user, subject="message2", pub_date=dj_timezone.now())
        pm2.send([self.third_user])

        pm3 = PrivateMessage(author=self.other_user, subject="message3", pub_date=dj_timezone.now())
        pm3.send([self.third_user])

        self.assertEqual(PrivateMessage.objects.count(), 3)
        self.assertEqual(PrivateMessageEntry.objects.count(), 6)

        pm2.refresh_from_db()
        pm2.privatemessageentry_set.all().delete()

        self.assertEqual(PrivateMessage.objects.count(), 3)
        self.assertEqual(PrivateMessageEntry.objects.count(), 4)

        pm3.privatemessageentry_set.filter(user=self.other_user).delete()

        self.assertEqual(PrivateMessage.objects.count(), 3)
        self.assertEqual(PrivateMessageEntry.objects.count(), 3)

        self.assertEqual(list(PrivateMessage.objects.orphan_messages()),[pm2])


class TestPrivateMessageEntry(TestCase):

    def setUp(self):
        super().setUp()

        user = User.objects.register_user('testing', 'example@example.com',
                                               'pwd', False)
        user.groups.add(Group.objects.get(name=settings.INYOKA_TEAM_GROUP_NAME))
        self.other_user = User.objects.register_user(
            'other_user',
            'example2@example.com',
            'pwd', False)
        pm = PrivateMessage(author=user, subject="Expired message", pub_date=dj_timezone.now() -
            timedelta(days=settings.PRIVATE_MESSAGE_INBOX_SENT_DURATION))
        pm.send([self.other_user])

        self.archive = PRIVMSG_FOLDERS["archive"][0]
        self.inbox = PRIVMSG_FOLDERS["inbox"][0]
        self.sent = PRIVMSG_FOLDERS["sent"][0]

        self.privmsgentry = PrivateMessageEntry.objects.get(message=pm, user=self.other_user)

    def test_delete_messages(self):
        self.assertEqual(self.privmsgentry.message.subject, 'Expired message')

        PrivateMessageEntry.clean_private_message_folders()

        self.assertFalse(PrivateMessageEntry.objects.filter(folder=self.inbox).exists())
        # Team members are spared
        self.assertTrue(PrivateMessageEntry.objects.filter(folder=self.sent).exists())
        self.assertEqual(PrivateMessage.objects.count(), 1)

    def test_delete_archived_messages(self):
        self.privmsgentry.archive()
        self.assertTrue(self.privmsgentry.in_archive)

        PrivateMessageEntry.clean_private_message_folders()

        self.assertTrue(PrivateMessageEntry.objects.filter(folder=self.archive, user=self.other_user).exists())
        self.assertEqual(PrivateMessage.objects.count(), 1)

    def test_private_messages_deleted(self):
        """
        remove user from team group, so clean_private_message_folders
         - clears all entries
         - deletes all private messages
        """
        u = User.objects.get(username='testing')
        u.groups.remove(Group.objects.get(name=settings.INYOKA_TEAM_GROUP_NAME))

        self.assertEqual(PrivateMessage.objects.count(), 1)

        PrivateMessageEntry.clean_private_message_folders()

        self.assertEqual(PrivateMessage.objects.count(), 0)


class TestSpamEmailAddress(TestCase):
    def test_str(self) -> None:
        address = SpamEmailAddress(email='test@inyoka.test')
        self.assertEqual(str(address), 'test@inyoka.test')

    @responses.activate
    def test_addresses_inserted(self) -> None:
        csv_buffer = io.StringIO()
        cwriter = csv.writer(csv_buffer)
        cwriter.writerow(['inyoka@inyoka.test', '1', '2026-08-23 15:17:11'])
        cwriter.writerow(['i@example.test', '5', '2026-08-18 14:31:38'])
        cwriter.writerow(['foobar97@test.test', '42', '2026-08-25 00:42:26'])

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'a') as zip_file:
            zip_file.writestr('listed_email_1_all.txt', csv_buffer.getvalue())

        rsp = responses.Response(
            method='GET',
            url='https://www.stopforumspam.com/downloads/listed_email_1_all.zip',
            content_type='application/zip',
            body=zip_buffer.getvalue(),
        )
        responses.add(rsp)

        SpamEmailAddress.objects.update_spam_emails()

        self.assertEqual(SpamEmailAddress.objects.count(), 3)
        self.assertCountEqual(
            SpamEmailAddress.objects.all().values_list('email', flat=True),
            ['inyoka@inyoka.test', 'i@example.test', 'foobar97@test.test'],
        )

        csv_buffer.close()
        zip_buffer.close()

    @responses.activate
    def test_addresses_invalid_email(self) -> None:
        csv_content = """email,other"""
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'a') as zip_file:
            zip_file.writestr('listed_email_1_all.txt', csv_content)

        rsp = responses.Response(
            method='GET',
            url='https://www.stopforumspam.com/downloads/listed_email_1_all.zip',
            content_type='application/zip',
            body=zip_buffer.getvalue(),
        )
        responses.add(rsp)

        with self.assertLogs(level=DEBUG) as cm:
            SpamEmailAddress.objects.update_spam_emails()

        self.assertEqual(SpamEmailAddress.objects.count(), 0)
        self.assertEqual(
            cm.output,
            [
                'INFO:inyoka:Starting update_spam_email_list',
                "DEBUG:inyoka:email: {'email': ['Enter a valid email address.']}",
                'INFO:inyoka:Finished update_spam_email_list',
            ],
        )

        zip_buffer.close()

    @responses.activate
    def test_addresses_email_already_in_db(self) -> None:
        csv_content = """test@email.test,other"""
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'a') as zip_file:
            zip_file.writestr('listed_email_1_all.txt', csv_content)

        rsp = responses.Response(
            method='GET',
            url='https://www.stopforumspam.com/downloads/listed_email_1_all.zip',
            content_type='application/zip',
            body=zip_buffer.getvalue(),
        )
        responses.add(rsp)
        responses.add(rsp)

        with self.assertLogs(level=DEBUG) as cm:
            SpamEmailAddress.objects.update_spam_emails()

        self.assertEqual(SpamEmailAddress.objects.count(), 1)
        self.assertEqual(
            cm.output,
            [
                'INFO:inyoka:Starting update_spam_email_list',
                'DEBUG:inyoka:Inserted test@email.test',
                'INFO:inyoka:Finished update_spam_email_list',
            ],
        )

        with self.assertLogs(level=DEBUG) as cm:
            SpamEmailAddress.objects.update_spam_emails()

        self.assertEqual(SpamEmailAddress.objects.count(), 1)
        self.assertEqual(
            cm.output,
            [
                'INFO:inyoka:Starting update_spam_email_list',
                'DEBUG:inyoka:test@email.test already in database',
                'INFO:inyoka:Finished update_spam_email_list',
            ],
        )

        zip_buffer.close()

    @responses.activate
    def test_addresses_fails__http_not_found(self) -> None:
        rsp = responses.Response(
            method='GET',
            url='https://www.stopforumspam.com/downloads/listed_email_1_all.zip',
            status=404,
        )
        responses.add(rsp)

        with self.assertLogs() as cm:
            SpamEmailAddress.objects.update_spam_emails()

        self.assertEqual(SpamEmailAddress.objects.count(), 0)
        self.assertEqual(
            cm.output,
            [
                'INFO:inyoka:Starting update_spam_email_list',
                'ERROR:inyoka:Failed to download spam list: 404 Client Error: Not Found for url: https://www.stopforumspam.com/downloads/listed_email_1_all.zip',
            ],
        )

    @responses.activate
    def test_bad_zipfile(self) -> None:
        rsp = responses.Response(
            method='GET',
            url='https://www.stopforumspam.com/downloads/listed_email_1_all.zip',
            content_type='application/zip',
            body='2',
        )
        responses.add(rsp)

        with self.assertLogs(level=DEBUG) as cm:
            SpamEmailAddress.objects.update_spam_emails()

        self.assertEqual(SpamEmailAddress.objects.count(), 0)
        self.assertEqual(
            cm.output,
            [
                'INFO:inyoka:Starting update_spam_email_list',
                'ERROR:inyoka:Received bad zip file from https://www.stopforumspam.com/downloads/listed_email_1_all.zip',
            ],
        )

    def test_old_entries_removed(self) -> None:
        with freeze_time('2007-11-17 00:00:00'):
            old = SpamEmailAddress.objects.create(email='old@inyoka.test')

        SpamEmailAddress.objects.create(email='recent@inyoka.test')

        self.assertEqual(SpamEmailAddress.objects.count(), 2)

        SpamEmailAddress.objects.prune_old_entries()

        self.assertEqual(SpamEmailAddress.objects.count(), 1)
        with self.assertRaises(SpamEmailAddress.DoesNotExist):
            old.refresh_from_db()
