#-*- coding: utf-8 -*-
"""
    tests.apps.portal.test_views
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test portal views.

    :copyright: (c) 2012-2015 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import re

from django.conf import settings
from django.test import TestCase
from django.core import mail
from django.utils import translation
from django.utils.timezone import now
from django.utils.translation import ugettext as _

from inyoka.utils.test import InyokaClient
from inyoka.portal.user import User, PERMISSION_NAMES
from inyoka.portal.models import (PrivateMessage, PrivateMessageEntry,
    Subscription, PRIVMSG_FOLDERS)
from inyoka.utils.storage import storage


class TestViews(TestCase):

    client_class = InyokaClient
    permissions = sum(PERMISSION_NAMES.keys())

    def setUp(self):
        self.user = User.objects.register_user('user', 'user@example.com', 'user', False)
        self.admin = User.objects.register_user('admin', 'admin', 'admin', False)
        self.admin._permissions = self.permissions
        self.admin.save()

        self.client.defaults['HTTP_HOST'] = settings.BASE_DOMAIN_NAME
        self.client.login(username='admin', password='admin')

    def test_group(self):
        """Test the creation of groups and if they handle invalid groupnames
        correctly.
        """
        storage['team_icon_height'] = 80
        storage['team_icon_width'] = 80

        postdata = {u'name': u'Lorem'}
        with translation.override('en-us'):
            response = self.client.post('/group/new/', postdata)
            self.assertEqual(response.status_code, 302)

        postdata = {u'name': u'LOr3m'}
        with translation.override('en-us'):
            response = self.client.post('/group/Lorem/edit/', postdata)
            self.assertNotIn(
                '<ul class="errorlist"><li>%s</li></ul>'
                % _(u'The group name contains invalid chars'),
                response.content.decode('utf-8')
            )

        postdata = {u'name': u'£Ø®€m'}
        with translation.override('en-us'):
            response = self.client.post('/group/LOr3m/edit/', postdata)
            self.assertIn(
                '<ul class="errorlist"><li>%s</li></ul>'
                % _(u'The group name contains invalid chars'),
                response.content.decode('utf-8')
            )

    def test_subscribe_user(self):
        """Test if it is possible to subscribe to users."""
        with translation.override('en-us'):
            response = self.client.post('/user/user/subscribe/', follow=True)
        self.assertRedirects(response, '/user/user/', host=settings.BASE_DOMAIN_NAME)
        self.assertIn(
            u'You will now be notified about activities of “user”.',
            response.content.decode('utf-8'),
        )
        self.assertTrue(Subscription.objects.user_subscribed(self.admin, self.user))

    def test_subscribe_user_as_unauthorized(self):
        """Make sure that unauthorized users can’t subscribe to other users"""
        with translation.override('en-us'):
            self.client.login(username='user', password='user')
            response = self.client.post('/user/admin/subscribe/')
            self.assertEqual(response.status_code, 403)
        self.assertFalse(Subscription.objects.user_subscribed(self.user, self.admin))

    def test_unsubscribe_user(self):
        """Test if it is possible to unsubscribe from users."""
        Subscription(user=self.admin, content_object=self.user).save()
        with translation.override('en-us'):
            response = self.client.post('/user/user/unsubscribe/', follow=True)
        self.assertRedirects(response, '/user/user/', host=settings.BASE_DOMAIN_NAME)
        self.assertIn(
            u'From now on you won’t be notified anymore about activities of “user”.',
            response.content.decode('utf-8'),
        )
        self.assertFalse(Subscription.objects.user_subscribed(self.admin, self.user))


class TestAuthViews(TestCase):

    client_class = InyokaClient

    def setUp(self):
        self.user = User.objects.register_user('user', 'user@example.com', 'user', False)
        self.client.defaults['HTTP_HOST'] = settings.BASE_DOMAIN_NAME

    def test_valid_login(self):
        """Test the login with valid credentials."""
        postdata = {'username': 'user', 'password': 'user'}
        with translation.override('en-us'):
            response = self.client.post('/login/', postdata, follow=True)
            self.assertRedirects(response, '/', host=settings.BASE_DOMAIN_NAME)
            self.assertInHTML('<div class="message success">%s</div>'
                              % _(u'You have successfully logged in.'),
                              response.content, count=1)

            self.assertTrue(response.client.session
                            .get_expire_at_browser_close())

            response = self.client.get('/login/', follow=True)
            self.assertRedirects(response, '/', host=settings.BASE_DOMAIN_NAME)
            self.assertInHTML('<div class="message error">%s</div>'
                              % _(u'You are already logged in.'),
                              response.content, count=1)

    def test_login_with_permanent_flag(self):
        """Test the “stay logged in” function."""
        postdata = {'username': 'user', 'password': 'user', 'permanent': 'on'}
        response = self.client.post('/login/', postdata, follow=True)
        self.assertRedirects(response, '/', host=settings.BASE_DOMAIN_NAME)

        self.assertFalse(self.client.session.get_expire_at_browser_close())
        self.assertEqual(self.client.session.get_expiry_age(),
                         settings.SESSION_COOKIE_AGE)

    def test_login_as_banned_user(self):
        """Maka sure that banned users can’t login."""
        banned_user = User.objects.register_user('badboy', 'bad', 'bad', False)
        banned_user.status = 2
        banned_user.save()

        postdata = {'username': 'badboy', 'password': 'bad'}
        with translation.override('en-us'):
            response = self.client.post('/login/', postdata)
            self.assertContains(response, 'is currently banned.')

    def test_login_as_inactive_user(self):
        """Make sure inactive users can’t login.

        Users who not confirmed their account via email are inactive and should
        not be able to login.
        """
        self.user.status = 0
        self.user.save()

        postdata = {'username': 'user', 'password': 'user'}
        with translation.override('en-us'):
            response = self.client.post('/login/', postdata)
            self.assertContains(response, 'is inactive.')

    def test_login_wrong_password(self):
        """Obviouly, a login should fail when a wrong password was submitted."""
        postdata = {'username': 'user', 'password': 'wrong_password'}
        with translation.override('en-us'):
            response = self.client.post('/login/', postdata)
        self.assertContains(response, 'Login failed because the password')

    def test_login_safe_redirects(self):
        """External redirects are not allowed after login.

        For convenience, users will be redirected to the page they came from
        after they logged in, but this does not include external pages. This
        test makes sure that such a redirect will fail while internal ones
        should work.
        """
        self.client.login(username='user', password='user')

        next = 'http://google.at'
        response = self.client.get('/login/', {'next': next}, follow=True)
        # We don't allow redirects to external pages!
        self.assertRedirects(response, '/', host=settings.BASE_DOMAIN_NAME)

        next = 'http://%s/calendar/' % settings.BASE_DOMAIN_NAME
        response = self.client.get('/login/', {'next': next}, follow=True)
        # But internal redirects are fine.
        self.assertRedirects(response, '/calendar/', host=settings.BASE_DOMAIN_NAME)

    def test_logout_as_anonymous(self):
        """If a user is logging out without beeing logged in previously,
        display a message telling that the user.
        """
        with translation.override('en-us'):
            response = self.client.get('/logout/', follow=True)
            self.assertContains(response, 'You were not logged in.')

    def test_logout(self):
        """Check if a session is properly cleaned up after a user requested a
        logout out of his account.
        """
        self.client.login(username='user', password='user')
        # Trigger a request to / to properly fill up the session.
        response = self.client.get('/')
        self.assertIn('_auth_user_id', self.client.session.keys())
        self.assertIn('_auth_user_backend', self.client.session.keys())

        next = 'http://%s/login/' % settings.BASE_DOMAIN_NAME
        response = self.client.get('/logout/', {'next': next})

        self.assertRedirects(response, '/login/', host=settings.BASE_DOMAIN_NAME)
        self.assertNotIn('_auth_user_id', self.client.session.keys())
        self.assertNotIn('_auth_user_backend', self.client.session.keys())

    def test_logout_safe_redirects(self):
        """External redirects are not allowed after logout.

        For convenience, users will be redirected to the page they came from
        after they logged out, but this does not include external pages. This
        test makes sure that such a redirect will fail while internal ones
        should work.
        """
        next = 'http://google.at'
        response = self.client.get('/logout/', {'next': next}, follow=True)
        # We don't allow redirects to external pages!
        self.assertRedirects(response, '/', host=settings.BASE_DOMAIN_NAME)

        next = 'http://%s/calendar/' % settings.BASE_DOMAIN_NAME
        response = self.client.get('/logout/', {'next': next}, follow=True)
        # But internal redirects are fine.
        self.assertRedirects(response, '/calendar/', host=settings.BASE_DOMAIN_NAME)

    def test_register_safe_redirects(self):
        """External redirects are not allowed after visiting the register page.

        For convenience, users will be redirected to the page they came from
        when they visited the register page, but this does not include external
        pages. This test makes sure that such a redirect will fail while
        internal ones should work.
        """
        self.client.login(username='user', password='user')
        next = 'http://google.at'
        response = self.client.get('/register/', {'next': next}, follow=True)
        # We don't allow redirects to external pages!
        self.assertRedirects(response, '/', host=settings.BASE_DOMAIN_NAME)

        next = 'http://%s/calendar/' % settings.BASE_DOMAIN_NAME
        response = self.client.get('/register/', {'next': next}, follow=True)
        # But internal redirects are fine.
        self.assertRedirects(response, '/calendar/', host=settings.BASE_DOMAIN_NAME)

    def test_register_as_authenticated_user(self):
        """Logged in users shall not be able to register a new account."""
        self.client.login(username='user', password='user')
        with translation.override('en-us'):
            response = self.client.get('/register/', follow=True)
        self.assertContains(response, 'You are already logged in.')

    def test_register(self):
        """Test the process of registering a new account.

        Checks if an email will be generated to activate the new account.
        """
        postdata = {
            'username': 'apollo13', 'password': 'secret',
            'confirm_password': 'secret', 'email': 'apollo13@example.com',
            'terms_of_usage': '1', 'captcha_1': ''
        }

        response = self.client.get('/', {'__service__': 'portal.get_captcha'})
        postdata['captcha_0'] = response._captcha_solution
        self.assertEqual(0, len(mail.outbox))
        with translation.override('en-us'):
            self.client.post('/register/', postdata)
        self.assertEqual(1, len(mail.outbox))
        subject = mail.outbox[0].subject
        self.assertIn(u'Activation of the user “apollo13”', subject)

    def test_lost_password(self):
        """Test the “lost password” feature.

        If a user forgot his password, he can use this feature to set a new
        one. This is done by generating a unique link and sending it to the
        emailaddress of the user. Check here if this email will be generated
        properly.
        """
        postdata = {'email': 'user@example.com'}
        with translation.override('en-us'):
            response = self.client.post('/lost_password/', postdata)
        subject = mail.outbox[0].subject
        self.assertIn(u'New password for “user”', subject)
        body = mail.outbox[0].body
        link = re.search(r'(/lost_password/.*)\n', body).groups()[0]
        with translation.override('en-us'):
            response = self.client.get(link)
        self.assertContains(response, 'You can set a new password')

    def test_lost_password_as_authenticated_user(self):
        """The “lost password” feature should not be available for logged in
        users.
        """
        self.client.login(username='user', password='user')
        with translation.override('en-us'):
            response = self.client.get('/lost_password/', follow=True)
        self.assertContains(response, 'You are already logged in.')

    def test_user_deactivate_and_recover(self):
        """Test the user deactivate and recover feature.
        """
        self.client.login(username='user', password='user')
        postdata = {'password_confirmation': 'user'}
        with translation.override('en-us'):
            response = self.client.post('/usercp/deactivate/', postdata, follow=True)
        self.assertContains(response, 'Your account was deactivated.')

        self.assertTrue(User.objects.get(pk=self.user.pk).is_deleted)

        # Once an account is deactivated the user session will be terminated.
        self.assertFalse(self.client.user.is_authenticated())

        subject = mail.outbox[0].subject
        self.assertIn(u'Deactivation of your account “user”', subject)
        code = re.search(r'^    [a-z0-9_-]+?:[a-z0-9_-]+?:[a-z0-9_-]+?$(?im)',
                         mail.outbox[0].body).group(0).strip()
        postdata = {'data': code}
        with translation.override('en-us'):
            response = self.client.post('/confirm/reactivate_user/', postdata, follow=True)
        self.assertContains(response, 'The account “user” was reactivated.')
        self.assertTrue(User.objects.get(pk=self.user.pk).is_active)

    def test_user_change_mail_and_recover(self):
        self.client.login(username='user', password='user')
        postdata = {'email': 'newmail@example.com'}
        with translation.override('en-us'):
            response = self.client.post('/usercp/profile/', postdata, follow=True)
        self.assertContains(response, 'You’ve been sent an email to confirm your new email address.')

        # Changing an email address requires a valid session
        self.client.logout()
        self.assertFalse(self.client.user.is_authenticated())

        # Perform invalid mail change
        subject = mail.outbox[0].subject
        self.assertIn(u'Confirm email address', subject)
        code = re.search(r'^    [a-z0-9_-]+?:[a-z0-9_-]+?:[a-z0-9_-]+?$(?im)',
                         mail.outbox[0].body).group(0).strip()
        postdata = {'data': code}
        with translation.override('en-us'):
            response = self.client.post('/confirm/set_new_email/', postdata, follow=True)
        self.assertContains(response, 'You need to be logged in before you can continue.')

        # Perform successful email change and log the user out again
        self.client.login(username='user', password='user')
        with translation.override('en-us'):
            response = self.client.post('/confirm/set_new_email/', postdata)
        self.client.logout()
        self.assertFalse(self.client.user.is_authenticated())

        # Perform invalid mail reset
        subject = mail.outbox[1].subject
        self.assertIn(u'Email address changed', subject)
        code = re.search(r'^    [a-z0-9_-]+?:[a-z0-9_-]+?:[a-z0-9_-]+?$(?im)',
                         mail.outbox[1].body).group(0).strip()
        postdata = {'data': code}
        with translation.override('en-us'):
            response = self.client.post('/confirm/reset_email/', postdata, follow=True)
        self.assertContains(response, 'You need to be logged in before you can continue.')

        # Perform successful email reset
        self.client.login(username='user', password='user')
        with translation.override('en-us'):
            response = self.client.post('/confirm/reset_email/', postdata)
        self.assertContains(response, 'Your email address was reset.')


class TestPrivMsgViews(TestCase):

    client_class = InyokaClient

    def setUp(self):
        self.user = User.objects.register_user('user', 'user@example.com', 'user', False)
        self.client.login(username='user', password='user')
        self.client.defaults['HTTP_HOST'] = settings.BASE_DOMAIN_NAME

    def test_access(self):
        response = self.client.get('/privmsg/', follow=True)
        self.assertRedirects(response, '/privmsg/inbox/',
                             host=settings.BASE_DOMAIN_NAME)
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/privmsg/inbox/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/privmsg/does_not_exist/')
        self.assertEqual(response.status_code, 404)

        response = self.client.get('/privmsg/42/')
        self.assertEqual(response.status_code, 404)

        response = self.client.get('/privmsg/', {'flavour': 'mobile'})
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/privmsg/42/', {'flavour': 'mobile'})
        self.assertEqual(response.status_code, 200)

    def test_delete_many(self):
        user2 = User.objects.register_user('user2', 'user2@example.com', 'user', False)
        pm1 = PrivateMessage.objects.create(author=user2, subject='Subject',
            text='Text', pub_date=now())
        PrivateMessageEntry.objects.create(message=pm1, user=user2,
            read=False, folder=PRIVMSG_FOLDERS['sent'][0])
        pme1 = PrivateMessageEntry.objects.create(message=pm1, user=self.user,
            read=False, folder=PRIVMSG_FOLDERS['inbox'][0])
        pm2 = PrivateMessage.objects.create(author=user2, subject='Subject',
            text='Text', pub_date=now())
        PrivateMessageEntry.objects.create(message=pm2, user=user2,
            read=False, folder=PRIVMSG_FOLDERS['sent'][0])
        pme2 = PrivateMessageEntry.objects.create(message=pm2, user=self.user,
            read=False, folder=PRIVMSG_FOLDERS['inbox'][0])

        # Check location and read status of new messages
        self.assertEqual(PrivateMessageEntry.objects.filter(user=self.user,
            folder=PRIVMSG_FOLDERS['inbox'][0]).count(), 2)
        self.assertEqual(PrivateMessageEntry.objects.filter(user=self.user,
            read=False).count(), 2)

        # Delete messages in inbox
        response = self.client.post('/privmsg/inbox/', {'delete': [pme1.pk, pme2.pk]})
        self.assertEqual(response.status_code, 302)

        # Check that deleted messages are in the trash and they are marked as read
        self.assertEqual(PrivateMessageEntry.objects.filter(user=self.user,
            folder=PRIVMSG_FOLDERS['trash'][0]).count(), 2)
        self.assertEqual(PrivateMessageEntry.objects.filter(user=self.user,
            read=True).count(), 2)

        # Permanently Delete messages in trash
        response = self.client.post('/privmsg/trash/', {'delete': [pme1.pk, pme2.pk]})
        self.assertEqual(response.status_code, 302)

        # Check that messages are not in any folder
        self.assertEqual(PrivateMessageEntry.objects.filter(user=self.user,
            folder__isnull=True).count(), 2)
        self.assertEqual(PrivateMessageEntry.objects.filter(user=self.user,
            read=True).count(), 2)
