# -*- coding: utf-8 -*-
"""
    inyoka.middlewares.session
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    A custom version of the session middleware that allows to set the
    session time (permanent, non permanent) on a session basis.  So users
    can decide to have a permanent session on login.

    Uses client side storage.

    :copyright: (c) 2007-2020 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import uuid
from time import time

from django.contrib.sessions import middleware

from inyoka.utils.sessions import is_permanent


class SessionMiddleware(middleware.SessionMiddleware):
    """
    Session middleware that allows you to turn individual browser-length
    sessions into persistent sessions and vice versa.

    This middleware can be used to implement the common "Remember Me" feature
    that allows individual users to decide when their session data is discarded.
    If a user ticks the "Remember Me" check-box on your login form create
    a persistent session, if they don't then create a browser-length session.
    """

    def process_request(self, request):
        super(SessionMiddleware, self).process_request(request)
        # Force creation of a session key so every browser is id-able.
        if not 'sid' in request.session:
            request.session['sid'] = str(uuid.uuid4())
            request.session.new = True
        else:
            request.session.new = False

    def process_response(self, request, response):
        if not hasattr(request, 'session'):
            return response

        # expire the surge protection information if there is one.
        # this keeps the cookie small
        surge_protection = request.session.get('sp')
        if surge_protection is not None:
            now = time()
            surge_protection = {key: timeout for key, timeout in
                                surge_protection.items() if timeout > now}
            if surge_protection:
                request.session['sp'] = surge_protection
            else:
                del request.session['sp']

        if request.session.modified:
            if is_permanent(request):
                request.session.set_expiry(None)
            else:
                # Require a session drop on browser close.
                request.session.set_expiry(0)

        return super(SessionMiddleware, self).process_response(request, response)
