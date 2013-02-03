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
        storage['team_icon_height'] = 80
        storage['team_icon_width'] = 80

        postdata = {u'name': u'Lorem'}
        with translation.override('en-us'):
            response = self.client.post('/group/new/', postdata)
            self.assertEqual(response.status_code, 302)

        postdata = {u'name': u'LOr3m'}
        with translation.override('en-us'):
            response = self.client.post('/group/Lorem/edit/', postdata)
            self.assertNotIn('<ul class="errorlist"><li>%s</li></ul>'
                % _(u'The group name contains invalid chars'),
                response.content.decode('utf-8'))

        postdata = {u'name': u'£Ø®€m'}
        with translation.override('en-us'):
            response = self.client.post('/group/LOr3m/edit/', postdata)
            self.assertIn('<ul class="errorlist"><li>%s</li></ul>'
                 % _(u'The group name contains invalid chars'),
                response.content.decode('utf-8'))

    def test_subscribe_user(self):
        with translation.override('en-us'):
            response = self.client.post('/user/user/subscribe/', follow=True)
        self.assertRedirects(response, '/user/user/', host=settings.BASE_DOMAIN_NAME)
        self.assertIn(
            u'You will now be notified about activities of “user”.',
            response.content.decode('utf-8'),
        )
        self.assertTrue(Subscription.objects.user_subscribed(self.admin, self.user))

    def test_subscribe_user_as_unauthorized(self):
        with translation.override('en-us'):
            self.client.login(username='user', password='user')
            response = self.client.post('/user/admin/subscribe/')
            self.assertEqual(response.status_code, 403)
        self.assertFalse(Subscription.objects.user_subscribed(self.user, self.admin))


class TestAuthViews(TestCase):

    client_class = InyokaClient

    def setUp(self):
        self.user = User.objects.register_user('user', 'user@example.com', 'user', False)
        self.client.defaults['HTTP_HOST'] = settings.BASE_DOMAIN_NAME

    def test_valid_login(self):
        postdata = {'username': 'user', 'password': 'user'}
        with translation.override('en-us'):
            response = self.client.post('/login/', postdata, follow=True)
            self.assertRedirects(response, '/', host=settings.BASE_DOMAIN_NAME)
            self.assertInHTML('<div class="message success">%s</div>'
                              % _(u'You have successfully logged in.'),
                              response.content, count=1)

            self.assertTrue(response.client.session \
                            .get_expire_at_browser_close())

            response = self.client.get('/login/', follow=True)
            self.assertRedirects(response, '/', host=settings.BASE_DOMAIN_NAME)
            self.assertInHTML('<div class="message error">%s</div>'
                              % _(u'You are already logged in.'),
                              response.content, count=1)

    def test_login_with_permanent_flag(self):
        postdata = {'username': 'user', 'password': 'user', 'permanent': 'on'}
        response = self.client.post('/login/', postdata, follow=True)
        self.assertRedirects(response, '/', host=settings.BASE_DOMAIN_NAME)

        self.assertFalse(self.client.session.get_expire_at_browser_close())
        self.assertEqual(self.client.session.get_expiry_age(),
                         settings.SESSION_COOKIE_AGE)

    def test_login_as_banned_user(self):
        banned_user = User.objects.register_user('badboy', 'bad', 'bad', False)
        banned_user.status = 2
        banned_user.save()

        postdata = {'username': 'badboy', 'password': 'bad'}
        with translation.override('en-us'):
            response = self.client.post('/login/', postdata)
            self.assertContains(response, 'is currently banned.')

    def test_login_as_inactive_user(self):
        self.user.status = 0
        self.user.save()

        postdata = {'username': 'user', 'password': 'user'}
        with translation.override('en-us'):
            response = self.client.post('/login/', postdata)
            self.assertContains(response, 'is inactive.')

    def test_login_wrong_password(self):
        postdata = {'username': 'user', 'password': 'wrong_password'}
        with translation.override('en-us'):
            response = self.client.post('/login/', postdata)
        self.assertContains(response, 'Login failed because the password')

    def test_login_safe_redirects(self):
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
        with translation.override('en-us'):
            response = self.client.get('/logout/', follow=True)
            self.assertContains(response, 'You were not logged in.')

    def test_logout(self):
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
        next = 'http://google.at'
        response = self.client.get('/logout/', {'next': next}, follow=True)
        # We don't allow redirects to external pages!
        self.assertRedirects(response, '/', host=settings.BASE_DOMAIN_NAME)

        next = 'http://%s/search/' % settings.BASE_DOMAIN_NAME
        response = self.client.get('/logout/', {'next': next}, follow=True)
        # But internal redirects are fine.
        self.assertRedirects(response, '/search/', host=settings.BASE_DOMAIN_NAME)

    def test_register_safe_redirects(self):
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
        self.client.login(username='user', password='user')
        with translation.override('en-us'):
            response = self.client.get('/register/', follow=True)
        self.assertContains(response, 'You are already logged in.')

    def test_register(self):
        postdata = {'username': 'apollo13', 'password': 'secret',
            'confirm_password': 'secret', 'email': 'apollo13@example.com',
            'terms_of_usage': '1'}

        self.assertEqual(0, len(mail.outbox))
        with translation.override('en-us'):
            response = self.client.post('/register/', postdata)
        self.assertEqual(1, len(mail.outbox))
        subject = mail.outbox[0].subject
        self.assertIn(u'Activation of the user “apollo13”', subject)

    def test_lost_password(self):
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
        self.client.login(username='user', password='user')
        with translation.override('en-us'):
            response = self.client.get('/lost_password/', follow=True)
        self.assertContains(response, 'You are already logged in.')
