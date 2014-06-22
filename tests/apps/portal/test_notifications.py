#-*- coding: utf-8 -*-
"""
    tests.apps.forum.test_views
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test forum views.

    :copyright: (c) 2012-2013 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL.
"""
import json

from django.core import mail
from django.test import TestCase
from django.utils import translation

from mock import patch

from inyoka.portal.user import (deactivate_user, send_activation_mail, set_new_email,
    send_new_email_confirmation, User)


def patched_signing_dumps(obj, **kwargs):
    data = {}
    data.update(obj)
    data.update(kwargs)
    return json.dumps(sorted(tuple(data.items())))


class TestNotifications(TestCase):

    def setUp(self):
        self.maxDiff = None
        self.user = User.objects.register_user('MyName', 'user@example.com', 'MyPass', False)

    def tearDown(self):
        # Make sure to clean the mail outbox after each test
        mail.outbox = []

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

    @patch('inyoka.portal.user.gen_activation_key', lambda x: 'a1b2c3')
    def test_send_activation_mail_en(self):
        with translation.override('en-us'):
            send_activation_mail(self.user)

        mail1 = mail.outbox[0]
        body = u'''Hello MyName,

welcome to inyoka.local!

Someone created an account using this email address (user@example.com) for account activation.

The account is still deactivated. To activate visit the following link: http://inyoka.local/activate/MyName/a1b2c3/

If you haven't registered the account yourself you can remove the account by visiting http://inyoka.local/delete/MyName/a1b2c3/

Due to security reasons we do not send your password as part of this email. We neither store the password in plain text in our database. Though, if you forget it someday we are only able to send you a new password.

NOTICE: Nobody will ever ask you for your password! Neither via email nor private message nor using any other contact form! Do not share the password with someone else!

As accepted during the registration process, every post you create at inyoka.local is licensed under http://inyoka.local/lizenz/

Kind regards and thank your for your participation.

Your inyoka.local team'''
        self.assertEqual(body, mail1.body)
        self.assertEqual(mail1.to, [u'user@example.com'])
        self.assertEqual(mail1.subject, u'inyoka.local – Activation of the user “MyName”')

    @patch('inyoka.portal.user.gen_activation_key', lambda x: 'a1b2c3')
    def test_send_activation_mail_de(self):
        with translation.override('de'):
            send_activation_mail(self.user)

        mail1 = mail.outbox[0]
        body = u'''Hallo MyName,

herzlich Willkommen bei inyoka.local!

Es wurde ein Benutzerkonto registriert, und diese E-Mail-Adresse (user@example.com) für die Bestätigung ausgewählt.

Das oben angesprochene Benutzerkonto ist im Moment inaktiv. Du kannst es erst benutzen, wenn du es durch Klicken auf folgenden Link aktiviert hast: http://inyoka.local/activate/MyName/a1b2c3/

Solltest du dieses Benutzerkonto nicht registriert haben, kannst du es unter folgendem Link wieder löschen: http://inyoka.local/delete/MyName/a1b2c3/

Aus Sicherheitsgründen schicken wir Dir Dein Passwort in dieser E-Mail nicht mit und speichern dieses auch nicht im Klartext in unserer Datenbank. Wenn Du es vergisst, können wir Dir also nur ein neues schicken.

Wichtiger Hinweis: Niemand wird Dich jemals (egal ob per E-Mail oder einer Privatnachricht oder sonst wie) nach Deinem Passwort fragen. Bitte halte dieses geheim und gib es nicht weiter!

Wenn Du selber Beiträge erstellst, unterliegen diese den Lizenzbedingungen von inyoka.local: http://inyoka.local/lizenz/

Vielen Dank für Deine Anmeldung!

Dein Team von inyoka.local'''
        self.assertEqual(body, mail1.body)
        self.assertEqual(mail1.to, [u'user@example.com'])
        self.assertEqual(mail1.subject, u'inyoka.local – Aktivierung des Benutzers „MyName“')

