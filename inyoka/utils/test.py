#-*- coding: utf-8 -*-
"""
    inyoka.utils.test
    ~~~~~~~~~~~~~~~~~

    Additional test tools and classes, like the InyokaClient
    for testing views including the user authentication.

    :copyright: (c) 2012 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from time import time
from django.conf import settings
from django.http import HttpRequest
from django.test.client import Client

from inyoka.middlewares.session import Session
from inyoka.portal.user import User


class InyokaClient(Client):
    """This test client inherits from :class:`django.test.client.Client` and
    allows us to keep track of the Inyoka session handling. Inyoka uses
    werkzeug's :class:`~werkzeug.contrib.securecookie.SecureCookie` to store
    the user's :attr:`~InyokaClient.session` on the client site.

    Additionally, the :class:`InyokaClient` implements a method
    :meth:`InyokaClient.set_host` to change the default host for the next
    requests.

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
            self.set_host(host)
        else:
            self.set_host(settings.BASE_DOMAIN_NAME)
        self.user = User.objects.get_anonymous_user()

    def set_host(self, host):
        """Set the default host for all further requests to ``host``.

        :param host: The default host

        """
        self.defaults['HTTP_HOST'] = host

    def login(self, user):
        """Try to Login ``user``

        :param user: The user to login
        :type user: :class:`inyoka.portal.user.User`
        :return: ``True`` in case the user is active, ``False`` otherwise.

        """

        assert isinstance(user, User)

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
