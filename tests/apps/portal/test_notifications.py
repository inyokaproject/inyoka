#-*- coding: utf-8 -*-
"""
    tests.apps.forum.test_views
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test forum views.

    :copyright: (c) 2012-2013 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL.
"""
import json

from django.conf import settings
from django.core import mail
from django.test import TestCase
from django.test.utils import override_settings
from django.utils import translation

from mock import patch

from inyoka.portal.user import (deactivate_user, set_new_email,
    send_new_email_confirmation, User)


def patched_signing_dumps(obj, **kwargs):
    data = {}
    data.update(obj)
    data.update(kwargs)
    return json.dumps(sorted(tuple(data.items())))


class TestNotifications(TestCase):

    def setUp(self):
        self.user = User.objects.register_user('MyName', 'user@example.com', 'MyPass', False)
        self.maxDiff = None

    def tearDown(self):
        # Make sure to clean the mail outbox after each test
        mail.outbox = []

    @override_settings(BASE_DOMAIN_NAME='inyoka.local')
    @patch('django.core.signing.dumps', patched_signing_dumps)
    def test_deactivate_user_en(self):
        self.assertEqual(len(mail.outbox), 0)
        with translation.override('en-us'):
            deactivate_user(self.user)

        mail1 = mail.outbox[0]
        body = u'''Hello MyName,

you have removed your user account from inyoka.local. To prevent abuse you are able to recreate your account within the next 30 days.

Please visit http://inyoka.local/confirm/reactivate_user/ and enter the following verification code:

    [["email", "user@example.com"], ["id", %d], ["salt", "inyoka.action.reactivate_user"], ["status", 1]]

Kind regards,

Your inyoka.local team''' % self.user.pk
        self.assertEqual(body, mail1.body)
        self.assertEqual(mail1.to, [u'user@example.com'])
        self.assertEqual(mail1.subject, u'Deactivation of your account “MyName” on inyoka.local')

    @override_settings(BASE_DOMAIN_NAME='inyoka.local')
    @patch('django.core.signing.dumps', patched_signing_dumps)
    def test_deactivate_user_de(self):
        with translation.override('de'):
            deactivate_user(self.user)

        mail1 = mail.outbox[0]
        body = u'''Hallo MyName,

du hast auf inyoka.local deinen Account gelöscht. Zum Schutz vor Missbrauch kannst du deinen Account wiederherstellen. Dies ist bis zu einen Monat ab heute möglich.

Besuche dazu http://inyoka.local/confirm/reactivate_user/ und gib die folgende Zeichenkette dort ein:

    [["email", "user@example.com"], ["id", %d], ["salt", "inyoka.action.reactivate_user"], ["status", 1]]

Dein Team von inyoka.local''' % self.user.pk
        self.assertEqual(body, mail1.body)
        self.assertEqual(mail1.to, [u'user@example.com'])
        self.assertEqual(mail1.subject, u'Deaktivierung deines Kontos „MyName“ auf inyoka.local')

    @override_settings(BASE_DOMAIN_NAME='inyoka.local')
    @patch('django.core.signing.dumps', patched_signing_dumps)
    def test_send_new_email_confirmation_en(self):
        self.assertEqual(len(mail.outbox), 0)
        with translation.override('en-us'):
            send_new_email_confirmation(self.user, 'new-mail@example.com')

        mail1 = mail.outbox[0]
        body = u'''Hello MyName,

we received a email change request for inyoka.local. To verify this request please visit http://inyoka.local/confirm/set_new_email/ and enter the following code:

    [["email", "new-mail@example.com"], ["id", %d], ["salt", "inyoka.action.set_new_email"]]

If you do not own the account on inyoka.local or if the change request was done by accident, you don't need to do anything. Your email address will not be used.

Kind regards,

Your inyoka.local team''' % self.user.pk
        self.assertEqual(body, mail1.body)
        self.assertEqual(mail1.to, [u'new-mail@example.com'])
        self.assertEqual(mail1.subject, u'inyoka.local – Confirm email address')

    @override_settings(BASE_DOMAIN_NAME='inyoka.local')
    @patch('django.core.signing.dumps', patched_signing_dumps)
    def test_send_new_email_confirmation_de(self):
        with translation.override('de'):
            send_new_email_confirmation(self.user, 'new-mail@example.com')

        mail1 = mail.outbox[0]
        body = u'''Hallo MyName,

du hast auf inyoka.local deine E-Mail-Adresse auf diese Adresse geändert. Damit diese Änderung aktiv wird, musst du sie bestätigen.

Besuche dazu http://inyoka.local/confirm/set_new_email/ und gib die folgende Zeichenkette dort ein:

    [["email", "new-mail@example.com"], ["id", %d], ["salt", "inyoka.action.set_new_email"]]

Falls dir dieses Konto auf inyoka.local nicht gehört oder du versehentlich deine E-Mail-Adresse geändert hastbrauchst du nichts weiter zu tun, deine E-Mail-Adresse wird nicht als Kontaktadresse verwendet werden.

Dein Team von inyoka.local''' % self.user.pk
        self.assertEqual(body, mail1.body)
        self.assertEqual(mail1.to, [u'new-mail@example.com'])
        self.assertEqual(mail1.subject, u'inyoka.local – E-Mail Adresse bestätigen')

    @override_settings(BASE_DOMAIN_NAME='inyoka.local')
    @patch('django.core.signing.dumps', patched_signing_dumps)
    def test_set_new_email_en(self):
        self.assertEqual(len(mail.outbox), 0)
        with translation.override('en-us'):
            set_new_email(self.user.pk, 'new-mail@example.com')

        mail1 = mail.outbox[0]
        body = u'''Hello MyName,

the email address of your account at inyoka.local has been changed to new-mail@example.com. To prevent abuse you can revert to your old email address by visiting http://inyoka.local/confirm/reset_email/ and entering the following code:

    [["email", "user@example.com"], ["id", %d], ["salt", "inyoka.action.reset_email"]]

You are only able to reset your email address withing the next 31 days.

NOTICE: In case of abuse you should change your password immediately! Keep in mind that nobody will ever ask you for your password! Neither via email nor private message nor using any other contact form! Do not share the password with someone else!

Kind regards,

Your inyoka.local team''' % self.user.pk
        self.assertEqual(body, mail1.body)
        self.assertEqual(mail1.to, [u'user@example.com'])
        self.assertEqual(mail1.subject, u'inyoka.local – Email address changed')

    @override_settings(BASE_DOMAIN_NAME='inyoka.local')
    @patch('django.core.signing.dumps', patched_signing_dumps)
    def test_set_new_email_de(self):
        with translation.override('de'):
            set_new_email(self.user.pk, 'new-mail@example.com')

        mail1 = mail.outbox[0]
        body = u'''Hallo MyName,

die E-Mail-Adresse deines Benutzers auf inyoka.local wurde auf new-mail@example.com geändert. Um Missbrauch zu vermeiden, kannst du die E-Mail-Adresse auf die alte zurücksetzen. Bitte beachte, dass das nur einen Monat ab heute möglich ist.

Besuche dazu die Seite http://inyoka.local/confirm/reset_email/ und gib folgende Zeichenkette dort ein:

    [["email", "user@example.com"], ["id", %d], ["salt", "inyoka.action.reset_email"]]

Im Falle eines Missbrauchs solltest du außerdem dein Passwort ändern. Wenn die Änderung der E-Mail-Adresse beabsichtigt war, brauchst du nichts weiter zu tun. Außer diese E-Mail zu löschen.

Dein Team von inyoka.local''' % self.user.pk
        self.assertEqual(body, mail1.body)
        self.assertEqual(mail1.to, [u'user@example.com'])
        self.assertEqual(mail1.subject, u'inyoka.local – E-Mail Adresse geändert')

