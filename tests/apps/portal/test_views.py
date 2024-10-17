"""
    tests.apps.portal.test_views
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test portal views.

    :copyright: (c) 2012-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import re

from django.conf import settings
from django.core import mail
from django.http import Http404
from django.test import RequestFactory
from django.test.utils import override_settings
from django.utils import translation
from django.utils.timezone import now
from django.utils.translation import gettext as _
from guardian.shortcuts import assign_perm

from inyoka.forum.models import Forum
from inyoka.portal.models import (
    PRIVMSG_FOLDERS,
    Linkmap,
    PrivateMessage,
    PrivateMessageEntry,
    StaticPage,
    Subscription,
)
from inyoka.portal.user import Group, User
from inyoka.portal.views import static_page
from inyoka.utils.test import InyokaClient, TestCase
from inyoka.utils.urls import href


class TestViews(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()
        self.user = User.objects.register_user('user', 'user@example.com', 'user', False)
        self.admin = User.objects.register_user('admin', 'admin', 'admin', False)
        self.admin.is_superuser = True
        self.admin.save()

        self.client.defaults['HTTP_HOST'] = settings.BASE_DOMAIN_NAME
        self.client.login(username='admin', password='admin')

    def test_group(self):
        """Test the creation of groups and if they handle invalid groupnames
        correctly.
        """

        postdata = {'name': 'Lorem'}
        with translation.override('en-us'):
            response = self.client.post('/group/new/', postdata)
            self.assertEqual(response.status_code, 302)

        postdata = {'name': 'LOr3m'}
        with translation.override('en-us'):
            response = self.client.post('/group/Lorem/edit/', postdata)
            self.assertNotIn(
                '<ul class="errorlist"><li>%s</li></ul>'
                % _('The group name contains invalid chars'),
                response.content.decode('utf-8')
            )

        postdata = {'name': '£Ø®€m'}
        with translation.override('en-us'):
            response = self.client.post('/group/LOr3m/edit/', postdata)
            self.assertIn(
                '<ul class="errorlist"><li>%s</li></ul>'
                % _('The group name contains invalid chars'),
                response.content.decode('utf-8')
            )

    def test_linkmap__without_permission(self):
        """Test if the link map throws 403 without permission"""
        self.client.login(username='user', password='user')
        response = self.client.get('/linkmap/')
        self.assertEqual(response.status_code, 403)

    def test_linkmap__with_permission(self):
        """Test if the link map site is reachable"""
        registered_group = Group.objects.get(name=settings.INYOKA_REGISTERED_GROUP_NAME)
        assign_perm('portal.change_linkmap', registered_group)

        self.client.login(username='user', password='user')
        response = self.client.get('/linkmap/')
        self.assertEqual(response.status_code, 200)

    def test_linkmap__post_valid(self):
        registered_group = Group.objects.get(name=settings.INYOKA_REGISTERED_GROUP_NAME)
        assign_perm('portal.change_linkmap', registered_group)
        self.client.login(username='user', password='user')

        data = {
            'form-TOTAL_FORMS': '3',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',

            'form-0-token': 'uu',
            'form-0-url': 'https://uu.test/',
            'form-0-icon': '',
        }
        response = self.client.post('/linkmap/', data=data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Linkmap.objects.count(), 1)

        css_name = Linkmap.objects.get_css_basename()
        self.assertIsNotNone(css_name)

    def test_linkmap__post_invalid(self):
        registered_group = Group.objects.get(name=settings.INYOKA_REGISTERED_GROUP_NAME)
        assign_perm('portal.change_linkmap', registered_group)
        self.client.login(username='user', password='user')

        data = {
            'form-TOTAL_FORMS': '3',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',

            'form-0-token': 'uu',
            'form-0-url': 'apt://uu.test/',  # invalid protocol
            'form-0-icon': '',
        }
        response = self.client.post('/linkmap/', data=data)
        self.assertIn(b'Enter a valid URL.', response.content)

    def test_linkmap_export(self):
        Linkmap.objects.create(token='uu', url='https://uu.test/')

        response = self.client.get('/linkmap/export/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'uu,https://uu.test/\r\n')

    def test_subscribe_user(self):
        """Test if it is possible to subscribe to users."""
        with translation.override('en-us'):
            response = self.client.post('/user/user/subscribe/', follow=True)
        self.assertRedirects(response, 'http://' + settings.BASE_DOMAIN_NAME + '/user/user/')
        self.assertIn(
            'You will now be notified about activities of “user”.',
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
        self.assertRedirects(response, 'http://' + settings.BASE_DOMAIN_NAME + '/user/user/')
        self.assertIn(
            'From now on you won’t be notified anymore about activities of “user”.',
            response.content.decode('utf-8'),
        )
        self.assertFalse(Subscription.objects.user_subscribed(self.admin, self.user))


class TestAuthViews(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()
        self.user = User.objects.register_user('user', 'user@example.com', 'user', False)

    def test_valid_login(self):
        """Test the login with valid credentials."""
        postdata = {'username': 'user', 'password': 'user'}
        with translation.override('en-us'):
            response = self.client.post('/login/', postdata, follow=True)
            self.assertRedirects(response, 'http://' + settings.BASE_DOMAIN_NAME + '/')
            self.assertInHTML('<div class="message success">%s</div>'
                              % _('You have successfully logged in.'),
                              response.content.decode(), count=1)

            self.assertTrue(response.client.session.get_expire_at_browser_close())

            response = self.client.get('/login/', follow=True)
            self.assertRedirects(response, 'http://' + settings.BASE_DOMAIN_NAME + '/')
            self.assertInHTML('<div class="message error">%s</div>'
                              % _('You are already logged in.'),
                              response.content.decode(), count=1)

    def test_valid_login__email(self):
        """Test the login with valid e-mail (instead of username)."""
        postdata = {'username': self.user.email, 'password': 'user'}
        with translation.override('en-us'):
            response = self.client.post('/login/', postdata, follow=True)
            self.assertRedirects(response, 'http://' + settings.BASE_DOMAIN_NAME + '/')
            self.assertInHTML('<div class="message success">%s</div>'
                              % _('You have successfully logged in.'),
                              response.content.decode(), count=1)

            self.assertTrue(response.client.session.get_expire_at_browser_close())

    def test_login_with_permanent_flag(self):
        """Test the “stay logged in” function."""
        postdata = {'username': 'user', 'password': 'user', 'permanent': 'on'}
        response = self.client.post('/login/', postdata, follow=True)
        self.assertRedirects(response, 'http://' + settings.BASE_DOMAIN_NAME + '/')

        self.assertFalse(self.client.session.get_expire_at_browser_close())
        self.assertEqual(self.client.session.get_expiry_age(),
                         settings.SESSION_COOKIE_AGE)

    def test_login_as_banned_user(self):
        """Make sure that banned users can’t login."""
        banned_user = User.objects.register_user('badboy', 'bad', 'bad', False)
        banned_user.status = User.STATUS_BANNED
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
        self.user.status = User.STATUS_INACTIVE
        self.user.save()

        postdata = {'username': 'user', 'password': 'user'}
        with translation.override('en-us'):
            response = self.client.post('/login/', postdata)
            self.assertContains(response, 'is inactive.')

    def test_login_invalid_password_hash(self):
        """Some users have a static string instead of a hash (as they still had unsafe password hashes). They should
         not be able to login. Instead, they should request a reset link via mail."""
        self.user.password = "was_sha1_until_2024"
        self.user.save()

        postdata = {'username': 'user', 'password': 'user'}
        with translation.override('en-us'):
            response = self.client.post('/login/', postdata)
            self.assertContains(response, 'Please enter a correct Username and password.')

        # try if mail is send out for reset link
        postdata = {'email': self.user.email}
        with translation.override('en-us'):
            self.client.post('/lost_password/', postdata)
        subject = mail.outbox[0].subject
        self.assertIn('New password for “user”', subject)

    def test_login_wrong_password(self):
        """Obviously, a login should fail when a wrong password was submitted."""
        postdata = {'username': 'user', 'password': 'wrong_password'}
        with translation.override('en-us'):
            response = self.client.post('/login/', postdata)
        self.assertContains(response, 'Please enter a correct')

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
        self.assertRedirects(response, 'http://' + settings.BASE_DOMAIN_NAME + '/')

        next = 'http://%s/calendar/' % settings.BASE_DOMAIN_NAME
        response = self.client.get('/login/', {'next': next}, follow=True)
        # But internal redirects are fine.
        self.assertRedirects(response, 'http://' + settings.BASE_DOMAIN_NAME + '/calendar/')

    def test_logout_as_anonymous(self):
        """If a user is logging out without being logged in previously,
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
        self.assertIn('_auth_user_id', list(self.client.session.keys()))
        self.assertIn('_auth_user_backend', list(self.client.session.keys()))

        next = 'http://%s/login/' % settings.BASE_DOMAIN_NAME
        response = self.client.get('/logout/', {'next': next})

        self.assertRedirects(response, 'http://' + settings.BASE_DOMAIN_NAME + '/login/')
        self.assertNotIn('_auth_user_id', list(self.client.session.keys()))
        self.assertNotIn('_auth_user_backend', list(self.client.session.keys()))

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
        self.assertRedirects(response, 'http://' + settings.BASE_DOMAIN_NAME + '/')

        next = 'http://%s/calendar/' % settings.BASE_DOMAIN_NAME
        response = self.client.get('/logout/', {'next': next}, follow=True)
        # But internal redirects are fine.
        self.assertRedirects(response, 'http://' + settings.BASE_DOMAIN_NAME + '/calendar/')

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
        self.assertRedirects(response, 'http://' + settings.BASE_DOMAIN_NAME + '/')

        next = 'http://%s/calendar/' % settings.BASE_DOMAIN_NAME
        response = self.client.get('/register/', {'next': next}, follow=True)
        # But internal redirects are fine.
        self.assertRedirects(response, 'http://' + settings.BASE_DOMAIN_NAME + '/calendar/')

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
        self.assertIn('Activation of the user “apollo13”', subject)

    def test_register_deactivated(self):
        """Test the process of registering a new account.

        Checks that a disabled registration doesn't allow registering new users.
        """
        with override_settings(INYOKA_DISABLE_REGISTRATION=True):
            with translation.override('en-us'):
                response = self.client.get('/register/', follow=True)
        self.assertRedirects(response, href('portal'))
        self.assertContains(response, 'User registration is currently disabled.')

    def test_register_contains_captcha(self):
        """The captcha is rendered via an own `ImageCaptchaWidget`"""
        response = self.client.get('/register/')
        self.assertContains(response, "__service__=portal.get_captcha")

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
        self.assertIn('New password for “user”', subject)
        body = mail.outbox[0].body
        link = re.search(r'(/lost_password/.*)\n', body).groups()[0]
        with translation.override('en-us'):
            response = self.client.get(link, follow=True)
        self.assertContains(response, 'You can set a new password')

    def test_lost_password_as_authenticated_user(self):
        """The “lost password” feature should not be available for logged in
        users.
        """
        self.client.login(username='user', password='user')
        with translation.override('en-us'):
            response = self.client.get('/lost_password/', follow=True)
        self.assertContains(response, 'You are already logged in.')

    def test_lost_password__banned_account(self):
        self.user.status = User.STATUS_BANNED
        self.user.save()

        self.client.post('/lost_password/', {'email': self.user.email})
        self.assertEqual(len(mail.outbox), 0)

    def test_lost_password__unusable_password(self):
        self.user.set_unusable_password()
        self.user.save()

        self.client.post('/lost_password/', {'email': self.user.email})
        self.assertEqual(len(mail.outbox), 0)

    def test_reactivate_user_as_authenticated_user(self):
        self.client.login(username='user', password='user')
        with translation.override('en-us'):
            response = self.client.get('/confirm/reactivate_user', follow=True)
        self.assertContains(response, 'You cannot reactivate an account while '
                            + 'you are logged in.', status_code=403)

    def test_confirm_direct_get_request(self):
        self.client.login(username='user', password='user')
        with translation.override('en-us'):
            response = self.client.get('/confirm/set_new_email/?token=ThisIsAToken')
        self.assertContains(response, 'ThisIsAToken')

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
        self.assertFalse(self.client.user.is_authenticated)

        subject = mail.outbox[0].subject
        self.assertIn('Deactivation of your account “user”', subject)
        code = re.search(r'(?im)^    [a-z0-9_-]+?:[a-z0-9_-]+?:[a-z0-9_-]+?$',
                         mail.outbox[0].body).group(0).strip()
        postdata = {'token': code}
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
        self.assertFalse(self.client.user.is_authenticated)

        # Perform mail change with invalid token
        self.client.login(username='user', password='user')
        postdata = {'token': 'ThisIsAWrongToken'}
        with translation.override('en-us'):
            response = self.client.post('/confirm/set_new_email/', postdata, follow=True)
        self.assertContains(response, 'The entered token is invalid or has expired.')
        self.client.logout()

        # Perform invalid mail change
        subject = mail.outbox[0].subject
        self.assertIn('Confirm email address', subject)
        code = re.search(r'(?im)^    [a-z0-9_-]+?:[a-z0-9_-]+?:[a-z0-9_-]+?$',
                         mail.outbox[0].body).group(0).strip()
        postdata = {'token': code}
        with translation.override('en-us'):
            response = self.client.post('/confirm/set_new_email/', postdata, follow=True)
        self.assertContains(response, 'You need to be logged in before you can continue.')

        # Perform successful email change and log the user out again
        self.client.login(username='user', password='user')
        with translation.override('en-us'):
            response = self.client.post('/confirm/set_new_email/', postdata)
        self.client.logout()
        self.assertFalse(self.client.user.is_authenticated)

        # Perform invalid mail reset
        subject = mail.outbox[1].subject
        self.assertIn('Email address changed', subject)
        code = re.search(r'(?im)^    [a-z0-9_-]+?:[a-z0-9_-]+?:[a-z0-9_-]+?$',
                         mail.outbox[1].body).group(0).strip()
        postdata = {'token': code}
        with translation.override('en-us'):
            response = self.client.post('/confirm/reset_email/', postdata, follow=True)
        self.assertContains(response, 'You need to be logged in before you can continue.')

        # Perform successful email reset
        self.client.login(username='user', password='user')
        with translation.override('en-us'):
            response = self.client.post('/confirm/reset_email/', postdata, follow=True)
        self.assertContains(response, 'Your email address was reset.')


class TestRegister(TestCase):

    client_class = InyokaClient
    username = 'Emma29'

    def setUp(self):
        super().setUp()
        self.url = '/register/'
        self.client.defaults['HTTP_HOST'] = settings.BASE_DOMAIN_NAME

    def test_get_status_code(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    @override_settings(PROPAGATE_TEMPLATE_CONTEXT=True)
    def post_username(self, form_username):
        User.objects.create(username=self.username)

        response = self.client.post(self.url, data={'username': form_username})
        return response.context['form']

    def test_username__invalid_characters(self):
        form = self.post_username(' ?')

        self.assertEqual(form.errors['username'],
                         ['Your username contains invalid characters. '
                          'Only alphanumeric chars and \u201c-\u201d are allowed.'])

    def test_username__exists_already(self):
        form = self.post_username(self.username)

        self.assertEqual(form.errors['username'],
                         ['This username is not available, please try another one.'])

    def test_username__exists_different_case(self):
        form = self.post_username(self.username.lower())

        self.assertEqual(form.errors['username'],
                         ['This username is not available, please try another one.'])

    def test_username__partly_same_exists(self):
        form = self.post_username(self.username[:-1])

        self.assertNotIn('username', form.errors)

    def test_username__prevent_email_address(self):
        form = self.post_username('foobar@inyoka.test')

        self.assertEqual(form.errors['username'],
                         ['Please do not enter an email address as username.'])


class TestPasswordChangeView(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()
        self.user = User.objects.register_user('user', 'user@example.test', 'user', False)

        self.client.defaults['HTTP_HOST'] = settings.BASE_DOMAIN_NAME
        self.client.login(username='user', password='user')

    def test_invalid__new_password_does_not_match_confirm(self):
        data = {'old_password': 'PASS123', 'new_password1': 'PASS456',
                'new_password2': 'XYZ'}
        response = self.client.post('/usercp/password/', data=data)
        self.assertIn(
            "The two password fields didn’t match.",
            response.content.decode('utf-8'),
        )

    def test_success_url(self):
        data = {"old_password": "user", "new_password1": "new", "new_password2": "new"}
        response = self.client.post('/usercp/password/', data=data, follow=True)

        self.assertRedirects(response, f'http://{settings.BASE_DOMAIN_NAME}/usercp/')
        self.assertIn(
            'Your password was changed successfully.',
            response.content.decode('utf-8'),
        )


class TestPrivMsgViews(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()
        self.user = User.objects.register_user('user', 'user@example.com', 'user', False)
        self.client.login(username='user', password='user')
        self.client.defaults['HTTP_HOST'] = settings.BASE_DOMAIN_NAME

    def test_access(self):
        response = self.client.get('/privmsg/', follow=True)
        self.assertRedirects(response, 'http://' + settings.BASE_DOMAIN_NAME + '/privmsg/inbox/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/privmsg/inbox/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/privmsg/does_not_exist/')
        self.assertEqual(response.status_code, 404)

        response = self.client.get('/privmsg/42/')
        self.assertEqual(response.status_code, 404)

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


class TestStaticPageView(TestCase):
    client_class = InyokaClient

    def test_returns_404_if_page_does_no_exist(self):
        request = RequestFactory().get('/')

        with self.assertRaises(Http404):
            static_page(request, 'should_no_exist')

    @override_settings(PROPAGATE_TEMPLATE_CONTEXT=True)
    def test_content(self):
        page = StaticPage.objects.create(key='foo', title='foo')
        response = self.client.get(page.get_absolute_url())

        self.assertEqual(response.context['title'], page.title)

    @override_settings(PROPAGATE_TEMPLATE_CONTEXT=True)
    def test_title(self):
        content = 'some random text'
        page = StaticPage.objects.create(key='foo', title='foo', content=content)
        response = self.client.get(page.get_absolute_url())

        self.assertIn(content, response.context['content'])


class TestStaticPageEdit(TestCase):
    client_class = InyokaClient

    def setUp(self):
        self.user = User.objects.register_user('user', 'user@example.com', 'user', False)
        self.client.login(username='user', password='user')

        self.page = StaticPage.objects.create(key='foo', title='foo')

    def test_status_code_with_permissions(self):
        registered_group = Group.objects.get(name=settings.INYOKA_REGISTERED_GROUP_NAME)
        assign_perm('portal.change_staticpage', registered_group)

        response = self.client.get(self.page.get_absolute_url('edit'))
        self.assertEqual(response.status_code, 200)

    def test_status_code_without_permissions(self):
        response = self.client.get(self.page.get_absolute_url('edit'))
        self.assertEqual(response.status_code, 403)

    def test_create_status_code_without_permissions(self):
        response = self.client.get(href('portal', 'page', 'new'))
        self.assertEqual(response.status_code, 403)

    def test_create_status_code_with_permissions(self):
        registered_group = Group.objects.get(name=settings.INYOKA_REGISTERED_GROUP_NAME)
        assign_perm('portal.change_staticpage', registered_group)

        response = self.client.get(href('portal', 'page', 'new'))
        self.assertEqual(response.status_code, 200)

    def test_create_page__object_in_db(self):
        registered_group = Group.objects.get(name=settings.INYOKA_REGISTERED_GROUP_NAME)
        assign_perm('portal.change_staticpage', registered_group)

        self.client.post(href('portal', 'page', 'new'),
                                    {'send': 'Send', 'title': 'foo2',
                                     'content': 'My great content'})

        StaticPage.objects.get(key='foo2')  # will raise an error, if missing

    def test_create_page__redirect_url(self):
        registered_group = Group.objects.get(name=settings.INYOKA_REGISTERED_GROUP_NAME)
        assign_perm('portal.change_staticpage', registered_group)

        response = self.client.post(href('portal', 'page', 'new'),
                                    {'send': 'Send', 'title': 'foo2',
                                     'content': 'My great content'})

        self.assertEqual(response.url, href('portal', 'foo2'))

    def test_create_page__success_message(self):
        registered_group = Group.objects.get(name=settings.INYOKA_REGISTERED_GROUP_NAME)
        assign_perm('portal.change_staticpage', registered_group)

        response = self.client.post(href('portal', 'page', 'new'),
                                    {'send': 'Send', 'title': 'foo2',
                                     'content': 'My great content'},
                                    follow=True)

        msg = 'The page “{}” was created successfully.'.format('foo2')
        self.assertContains(response, msg)

    def test_edit_page__success_message(self):
        registered_group = Group.objects.get(name=settings.INYOKA_REGISTERED_GROUP_NAME)
        assign_perm('portal.change_staticpage', registered_group)

        new_title = 'foo2'
        response = self.client.post(self.page.get_absolute_url('edit'),
                                    {'send': 'Send', 'title': new_title,
                                     'content': 'My great content',
                                     'key': self.page.key}, follow=True)

        msg = f'The page “{new_title}” was changed successfully.'
        self.assertContains(response, msg)

    def test_edit_page__redirect_url(self):
        registered_group = Group.objects.get(name=settings.INYOKA_REGISTERED_GROUP_NAME)
        assign_perm('portal.change_staticpage', registered_group)

        new_title = 'foo2'
        response = self.client.post(self.page.get_absolute_url('edit'),
                                    {'send': 'Send', 'title': new_title,
                                     'content': 'My great content',
                                     'key': self.page.key})

        self.assertEqual(response.url, href('portal', self.page.key))

    def test_preview(self):
        registered_group = Group.objects.get(name=settings.INYOKA_REGISTERED_GROUP_NAME)
        assign_perm('portal.change_staticpage', registered_group)

        content = 'My great content'
        response = self.client.post(href('portal', 'page', 'new'),
                                    {'preview': 'Preview', 'title': 'foo3',
                                     'content': content})

        self.assertContains(response, content)
        self.assertContains(response, '<div class="preview">')


class TestEditGlobalPermissions(TestCase):
    client_class = InyokaClient

    @staticmethod
    def get_url(group_name):
        return href('portal', 'group', group_name, 'edit', 'global_permissions')

    def setUp(self):
        self.user = User.objects.register_user('user', 'user@example.local', 'user', False)
        self.client.login(username='user', password='user')

        self.group = Group.objects.get(name=settings.INYOKA_REGISTERED_GROUP_NAME)
        self.url = self.get_url(self.group.name)

    def _permissions_for_user(self):
        assign_perm('auth.change_group', self.group)

    def test_anonymous_user(self):
        response = self.client_class().get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith("/login/?next=/group/registered/edit/global_permissions/"))

    def test_missing_permissions(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_not_existing_group__404(self):
        self._permissions_for_user()
        self.url = self.get_url('not_existing')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_get(self):
        self._permissions_for_user()
        response = self.client.get(self.url)

        self.assertContains(response,
                            '<input type="checkbox" name="auth_permissions" value="auth.change_group"')


class TestEditForumPermissions(TestCase):
    client_class = InyokaClient

    @staticmethod
    def get_url(group_name):
        return href('portal', 'group', group_name, 'edit', 'forum_permissions')

    def setUp(self):
        self.user = User.objects.register_user('user', 'user@example.local', 'user', False)
        self.client.login(username='user', password='user')

        self.group = Group.objects.get(name=settings.INYOKA_REGISTERED_GROUP_NAME)
        self.url = self.get_url(self.group.name)

    def _permissions_for_user(self):
        assign_perm('auth.change_group', self.group)

    def test_anonymous_user(self):
        response = self.client_class().get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith("/login/?next=/group/registered/edit/forum_permissions/"))

    def test_missing_permissions(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_not_existing_group__404(self):
        self._permissions_for_user()
        self.url = self.get_url('not_existing')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_get(self):
        forum = Forum.objects.create(name='Forum 1')
        self._permissions_for_user()
        response = self.client.get(self.url)

        self.assertContains(response, forum.name, html=True)
