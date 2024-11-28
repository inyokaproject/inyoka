"""
    tests.apps.portal.test_models
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test portal models.

    :copyright: (c) 2012-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import gzip
from datetime import datetime, timedelta
from os import path

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from inyoka.portal.models import (
    PRIVMSG_FOLDERS,
    Linkmap,
    PrivateMessage,
    PrivateMessageEntry,
)
from inyoka.portal.user import User
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
            css = '/* linkmap for inter wiki links \n :license: BSD*/a.interwiki-example {padding-left: 20px; background-image: url("%s"); }'
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
        pm = PrivateMessage(author=user, subject="Expired message", pub_date=datetime.now() -
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

    def test_delete_archived_messages(self):
        self.privmsgentry.archive()
        self.assertTrue(self.privmsgentry.in_archive)
        PrivateMessageEntry.clean_private_message_folders()
        self.assertTrue(PrivateMessageEntry.objects.filter(folder=self.archive, user=self.other_user).exists())
