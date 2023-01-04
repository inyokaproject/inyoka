# -*- coding: utf-8 -*-
"""
    inyoka.testing
    ~~~~~~~~~~~~~~

    Various utilities and helpers that improve our unittest experience.

    :copyright: (c) 2007-2023 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import gc
from importlib import import_module

import responses
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.core.cache import caches
from django.http import HttpRequest
from django.test import TestCase as _TestCase
from django.test.client import Client

from inyoka.portal.user import User
from inyoka.utils.spam import (
    get_comment_check_url,
    get_mark_ham_url,
    get_mark_spam_url,
    get_verify_key_url,
)


def profile_memory(func):
    # run the test 50 times.  if length of gc.get_objects()
    # keeps growing, assert false

    def profile(*args):
        gc.collect()
        samples = [0 for x in range(0, 50)]
        for x in range(0, 50):
            func(*args)
            gc.collect()
            samples[x] = len(gc.get_objects())

        for x in samples[-4:]:
            if x != samples[-5]:
                flatline = False
                break
        else:
            flatline = True

        # object count is bigger than when it started
        if not flatline and samples[-1] > samples[0]:
            for x in samples[1:-2]:
                # see if a spike bigger than the endpoint exists
                if x > samples[-1]:
                    break
            else:
                assert False, repr(samples) + " " + repr(flatline)

    return profile


class InyokaClient(Client):
    """
    In order to change the requesting host, use::

        client.defaults['HTTP_HOST'] = 'url.example.com'

    """

    def __init__(self, enforce_csrf_checks=False, host=None, **defaults):
        """Update the default request variables with ``**defaults`` and disable
        CSRF checks by default. If ``host`` is given, this host is set as
        default for further request. The user of this client is an instance of
        :class:`inyoka.portal.user.User` and :data:`ANONYMOUS_USER_NAME` by
        default. To change the user, call :meth:`InyokaClient.login(user)`.

        """
        super(InyokaClient, self).__init__(enforce_csrf_checks, **defaults)
        if isinstance(host, str):
            self.defaults['HTTP_HOST'] = host
        else:
            self.defaults['HTTP_HOST'] = settings.BASE_DOMAIN_NAME
        self.user = User.objects.get_anonymous_user()

    def login(self, **credentials):
        """Try to authenticate a user with username and password.

        :param username: The username of the :class:`~inyoka.portal.user.User`
            to login
        :param password: The password of the user to login
        :type username: string
        :type password: string
        :raise:
            User.DoesNotExist
                If the user with `username` does not exist
            :class:`~inyoka.portal.user.UserBanned`
                If the found user is banned
        :return: ``True`` in case the described user can be logged in, and is
            active, ``False`` otherwise.

        """

        user = authenticate(**credentials)
        if user.is_active:
            engine = import_module(settings.SESSION_ENGINE)

            # Create a fake request to store login details.
            request = HttpRequest()
            if self.session:
                request.session = self.session
            else:
                request.session = engine.SessionStore()
            login(request, user)

            # Save the session values.
            request.session.save()

            # Set the cookie to represent the session.
            session_cookie = settings.SESSION_COOKIE_NAME
            self.cookies[session_cookie] = request.session.session_key
            cookie_data = {
                'max-age': None,
                'path': '/',
                'domain': settings.SESSION_COOKIE_DOMAIN,
                'secure': settings.SESSION_COOKIE_SECURE or None,
                'expires': None,
            }
            self.cookies[session_cookie].update(cookie_data)

            return True
        else:
            return False


class AntiSpamTestCaseMixin(object):

    def make_valid_key(self):
        responses.add(
            responses.POST, get_verify_key_url(), body='valid', status=200,
            content_type='text/plain'
        )

    def make_spam(self):
        responses.add(
            responses.POST, get_comment_check_url(), body='true', status=200,
            content_type='text/plain'
        )

    def make_mark_ham(self):
        responses.add(
            responses.POST, get_mark_ham_url(), body='Thank you', status=200,
            content_type='text/plain'
        )

    def make_mark_spam(self):
        responses.add(
            responses.POST, get_mark_spam_url(), body='Thank you', status=200,
            content_type='text/plain'
        )


class TestCase(_TestCase):
    """
    Default TestCase for all Inyoka tests.

    Deletes the content cache after each run.
    """

    def _post_teardown(self):
        super(TestCase, self)._post_teardown()
        content_cache = caches['content']
        content_cache.delete_pattern("*")
        default_cache = caches['default']
        default_cache.delete_pattern("*")
