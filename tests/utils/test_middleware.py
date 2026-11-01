"""
tests.apps.utils.test_middleware
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test Inyoka-custom middlewares.

:copyright: (c) 2012-2026 by the Inyoka Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from django.conf import settings
from django.contrib import auth
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponseNotFound
from django.test import RequestFactory

from inyoka.middlewares.auth import AuthMiddleware
from inyoka.middlewares.common import CommonServicesMiddleware
from inyoka.portal.user import User
from inyoka.utils.test import InyokaClient, TestCase


class TestNULByte(TestCase):
    client_class = InyokaClient

    def test_get_null(self):
        url = f'http://{settings.BASE_DOMAIN_NAME}/1%00%EF/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_get_null_calender(self):
        url = (
            f'http://{settings.BASE_DOMAIN_NAME}/2023/11/18/lpd-2023-10\x00EF2522/ics/'
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)


class TestServiceMiddleware(TestCase):
    def test_invalid_module(self):
        url = f'http://{settings.BASE_DOMAIN_NAME}/?__service__=%40%40rKhiI&component=&hide='
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_http_not_found(self):
        url = f'http://{settings.BASE_DOMAIN_NAME}/?__service__=portal.toggle_sidebar%27%7C%7CDBMS_PIPE.RECEIVE'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_control_characters_stripped_in_post(self):
        self.factory = RequestFactory()
        data = {'foobar': 'control characters \x08 \x0f in text'}
        request = self.factory.post('/', data)
        CommonServicesMiddleware(lambda x: x).process_request(request)
        self.assertEqual(request.POST['foobar'], 'control characters   in text')


class TestAuthMiddleware(TestCase):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.middleware = AuthMiddleware(lambda x: HttpResponseNotFound())
        self.anonymous_user = User.objects.get_anonymous_user()

    def _make_request(self):
        request = self.factory.get('/')
        request.subdomain = ''
        SessionMiddleware(lambda _request: None).process_request(request)
        request.session['sid'] = 'test-session'
        request.session.new = False

        setattr(request, '_messages', FallbackStorage(request))
        return request

    def _set_user_session(self, request, user, valid_hash=True):
        request.session[auth.SESSION_KEY] = user.pk
        request.session[auth.BACKEND_SESSION_KEY] = user.backend
        request.session[auth.HASH_SESSION_KEY] = (
            user.get_session_auth_hash() if valid_hash else 'invalid-session-hash'
        )
        request.session.modified = True
        return request

    def test_process_request_uses_authenticated_user_with_valid_session(self):
        user = User.objects.register_user(
            'alice', 'alice@example.test', 'secret', send_mail=False
        )

        request = self._make_request()
        self._set_user_session(request, user, valid_hash=True)

        self.middleware.process_request(request)

        self.assertEqual(request.user, user)
        self.assertTrue(request.user.is_authenticated)
        self.assertEqual(request.session['sid'], 'test-session')

    def test_process_request_uses_anonymous_user_when_session_is_missing(self):
        request = self._make_request()

        self.middleware.process_request(request)

        self.assertEqual(request.user, self.anonymous_user)
        self.assertFalse(request.user.is_authenticated)

    def test_process_request_uses_anonymous_user_when_backend_returns_no_user(self):
        request = self._make_request()
        request.session[auth.SESSION_KEY] = 999999
        request.session[auth.BACKEND_SESSION_KEY] = (
            'inyoka.portal.auth.InyokaAuthBackend'
        )
        request.session[auth.HASH_SESSION_KEY] = 'irrelevant'
        request.session.modified = True

        self.middleware.process_request(request)

        self.assertEqual(request.user, self.anonymous_user)
        self.assertFalse(request.user.is_authenticated)

    def test_process_request_invalidates_session_when_hash_is_invalid(self):
        user = User.objects.register_user(
            'bob', 'bob@example.test', 'secret', send_mail=False
        )

        request = self._make_request()
        self._set_user_session(request, user, valid_hash=False)

        self.middleware.process_request(request)

        self.assertEqual(request.user, self.anonymous_user)
        self.assertTrue(request.session.new)
        self.assertIn('sid', request.session)
        self.assertIsInstance(request.session['sid'], str)
        self.assertEqual(len(request.session['sid']), 36)

    def test_process_request_banned_user_is_anonymized_and_message_is_added(self):
        user = User.objects.register_user(
            'banned-user', 'banned@example.test', 'secret', send_mail=False
        )
        user.status = User.STATUS_BANNED
        user.save()

        request = self._make_request()
        self._set_user_session(request, user, valid_hash=True)

        self.middleware.process_request(request)

        self.assertEqual(request.user, self.anonymous_user)
        self.assertNotIn('_auth_user_id', request.session)
        self.assertEqual(
            ['The user “banned-user” was banned. Your session has ended.'],
            [m.message for m in get_messages(request)],
        )

    def test_process_request_deleted_user_is_anonymized_and_message_is_added(self):
        user = User.objects.register_user(
            'deleted-user', 'deleted@example.test', 'secret', send_mail=False
        )
        user.status = User.STATUS_DELETED
        user.save()

        request = self._make_request()
        self._set_user_session(request, user, valid_hash=True)

        self.middleware.process_request(request)

        self.assertEqual(request.user, self.anonymous_user)
        self.assertNotIn('_auth_user_id', request.session)
        self.assertEqual(
            ['The user “deleted-user” deleted his profile. Your session has ended.'],
            [m.message for m in get_messages(request)],
        )
