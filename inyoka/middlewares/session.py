# -*- coding: utf-8 -*-
"""
    inyoka.middlewares.session
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    A custom version of the session middleware that allows to set the
    session time (permanent, non permanent) on a session basis.  So users
    can decide to have a permanent session on login.

    To control the session system use the `make_permanet` and
    `close_with_browser` functions of the `inyoka.utils.sessions` module.

    Uses client side storage.


    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from hashlib import md5
from time import time
from random import random
from django.conf import settings
from django.utils.translation import ugettext as _
from werkzeug import cookie_date
from werkzeug.contrib.securecookie import SecureCookie
from inyoka.utils.flashing import flash


class Session(SecureCookie):

    @property
    def session_key(self):
        if 'uid' in self:
            self.pop('_sk', None)
            return self['uid']
        elif not '_sk' in self:
            self['_sk'] = md5('%s%s%s' % (random(), time(),
                              settings.SECRET_KEY)).digest() \
                              .encode('base64').strip('\n =')
        return self['_sk']


class AdvancedSessionMiddleware(object):
    """
    Session middleware that allows you to turn individual browser-length
    sessions into persistent sessions and vice versa.

    This middleware can be used to implement the common "Remember Me" feature
    that allows individual users to decide when their session data is discarded.
    If a user ticks the "Remember Me" check-box on your login form create
    a persistent session, if they don't then create a browser-length session.
    """

    def process_request(self, request):
        data = request.COOKIES.get(settings.SESSION_COOKIE_NAME)
        session = None
        expired = False
        if data:
            session = Session.unserialize(data, settings.SECRET_KEY)
            if session.get('_ex', 0) < time():
                session = None
                expired = True
        if session is None:
            session = Session(secret_key=settings.SECRET_KEY)
            session['_ex'] = time() + settings.SESSION_COOKIE_AGE
        request.session = session
        if expired:
            flash(_(u'Your session expired.  You need to login again'),
                  session=session)

    def process_response(self, request, response):
        try:
            modified = request.session.modified
        except AttributeError:
            return response

        # expire the surge protection information if there is one.
        # this keeps the cookie small
        surge_protection = request.session.get('sp')
        if surge_protection is not None:
            now = time()
            surge_protection = {key: timeout for key, timeout in
                                surge_protection.iteritems() if timeout > now}
            if surge_protection:
                request.session['sp'] = surge_protection
            else:
                del request.session['sp']

        # we can remove the session key if the user is logged in
        if '_sk' in request.session and 'uid' in request.session:
            del request.session['_sk']

        if modified or settings.SESSION_SAVE_EVERY_REQUEST:
            if request.session.get('_perm'):
                expires_time = request.session.get('_ex', 0)
                expires = cookie_date(expires_time)
            else:
                expires = None
            response.set_cookie(settings.SESSION_COOKIE_NAME,
                                request.session.serialize(),
                                expires=expires,
                                domain=settings.SESSION_COOKIE_DOMAIN,
                                secure=settings.SESSION_COOKIE_SECURE or None)
        return response
