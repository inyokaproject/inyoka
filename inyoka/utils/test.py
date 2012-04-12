#-*- coding: utf-8 -*-
"""
    inyoka.testing
    ~~~~~~~~~~~~~~

    Various utilities and helpers that improve our unittest experience.

    :copyright: (c) 2007-2012 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import gc
from copy import copy
from time import time
from functools import wraps

from django.conf import settings, UserSettingsHolder
from django.db import connection
from django.http import HttpRequest
from django.test.client import Client

from inyoka.portal.user import User

# FIXME:
class Session(object):
    def __init__(self, d, secret_key):
        self.data = d
        self.secret_key = secret_key


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

        print "sample gc sizes:", samples

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
