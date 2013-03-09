#-*- coding: utf-8 -*-
"""
    tests.functional.apps.portal.test_views
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test portal views.

    :copyright: (c) 2012-2013 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL.
"""
import re

from django.conf import settings
from django.core import mail
from django.test import TestCase

from django.utils import translation
from django.utils.translation import ugettext as _

from inyoka.portal.models import Subscription
from inyoka.portal.user import User, PERMISSION_NAMES
from inyoka.utils.storage import storage
from inyoka.utils.test import InyokaClient


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
        """Test the ”stay logged in” function."""
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

        next = 'http://%s/search/' % settings.BASE_DOMAIN_NAME
        response = self.client.get('/login/', {'next': next}, follow=True)
        # But internal redirects are fine.
        self.assertRedirects(response, '/search/', host=settings.BASE_DOMAIN_NAME)

    def test_logout_as_anonymous(self):
        """If a user is logging out without beeing logged in previousley,
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

        next = 'http://%s/search/' % settings.BASE_DOMAIN_NAME
        response = self.client.get('/logout/', {'next': next}, follow=True)
        # But internal redirects are fine.
        self.assertRedirects(response, '/search/', host=settings.BASE_DOMAIN_NAME)

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

        next = 'http://%s/search/' % settings.BASE_DOMAIN_NAME
        response = self.client.get('/register/', {'next': next}, follow=True)
        # But internal redirects are fine.
        self.assertRedirects(response, '/search/', host=settings.BASE_DOMAIN_NAME)

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
            'terms_of_usage': '1'
        }

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
