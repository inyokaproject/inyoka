#-*- coding: utf-8 -*-
"""
    inyoka.utils.test
    ~~~~~~~~~~~~~~~~~

    Additional test tools and classes, like the InyokaClient
    for testing views including the user authentication.

    :copyright: (c) 2012 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from copy import copy
from time import time
from functools import wraps
from django.conf import settings, UserSettingsHolder
from django.http import HttpRequest
from django.test.client import Client

from inyoka.middlewares.session import Session
from inyoka.portal.user import User


class InyokaClient(Client):
    """This test client inherits from :class:`django.test.client.Client` and
    allows us to keep track of the Inyoka session handling. Inyoka uses
    werkzeug's :class:`~werkzeug.contrib.securecookie.SecureCookie` to store
    the user's :attr:`~InyokaClient.session` on the client site.

    In order to change the requesting host, use::

        client.defaults['HTTP_HOST'] = 'url.example.com'

    """

    #: The session instance to be used in this client.
    session = Session({}, secret_key=settings.SECRET_KEY)

    def __init__(self, enforce_csrf_checks=False, host=None, **defaults):
        """Update the default request variables with ``**defaults`` and disable
        CSRF checks by default. If ``host`` is given, this host is set as
        default for further request. The user of this client is an instance of
        :class:`inyoka.portal.user.User` and :data:`INYOKA_ANONYMOUS_USER` by
        default. To change the user, call :meth:`InyokaClient.login(user)`.

        """
        super(InyokaClient, self).__init__(enforce_csrf_checks, **defaults)
        if isinstance(host, basestring):
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

        username = credentials.get('username', None)
        password = credentials.get('password', None)
        assert username is not None
        assert password is not None

        user = User.objects.authenticate(username, password)
        if user.is_active:
            request = HttpRequest()
            if self.session:
                request.session = self.session
            else:
                request.session = Session({}, secret_key=settings.SECRET_KEY)
            user.login(request)

            session_cookie = settings.SESSION_COOKIE_NAME
            self.session = request.session
            self.session['_ex'] = time() + 3600
            self.cookies[session_cookie] = self.session.serialize()
            cookie_data = {
                'max-age': 999999999,
                'path': '/',
                'domain': settings.SESSION_COOKIE_DOMAIN,
                'secure': settings.SESSION_COOKIE_SECURE or None,
                'expires': None,
            }
            self.cookies[session_cookie].update(cookie_data)
            self.user = user

            return True
        else:
            return False


#XXX 1.4: Copied from Django1.4, can be removed once we upgrade
class override_settings(object):
    """
    Acts as either a decorator, or a context manager. If it's a decorator it
    takes a function and returns a wrapped function. If it's a contextmanager
    it's used with the ``with`` statement. In either event entering/exiting
    are called before and after, respectively, the function/block is executed.
    """
    def __init__(self, **kwargs):
        self.options = kwargs
        self.wrapped = settings._wrapped

    def __enter__(self):
        self.enable()

    def __exit__(self, exc_type, exc_value, traceback):
        self.disable()

    def __call__(self, test_func):
        from django.test import TransactionTestCase
        if isinstance(test_func, type) and issubclass(test_func, TransactionTestCase):
            original_pre_setup = test_func._pre_setup
            original_post_teardown = test_func._post_teardown
            def _pre_setup(innerself):
                self.enable()
                original_pre_setup(innerself)
            def _post_teardown(innerself):
                original_post_teardown(innerself)
                self.disable()
            test_func._pre_setup = _pre_setup
            test_func._post_teardown = _post_teardown
            return test_func
        else:
            @wraps(test_func)
            def inner(*args, **kwargs):
                with self:
                    return test_func(*args, **kwargs)
        return inner

    def enable(self):
        override = UserSettingsHolder(settings._wrapped)
        for key, new_value in self.options.items():
            setattr(override, key, new_value)
        settings._wrapped = override

    def disable(self):
        settings._wrapped = self.wrapped
        for key in self.options:
            new_value = getattr(settings, key, None)
