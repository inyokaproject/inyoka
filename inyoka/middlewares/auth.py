#-*- coding: utf-8 -*-
"""
    inyoka.middlewares.auth
    ~~~~~~~~~~~~~~~~~~~~~~~

    This replaces the django auth middleware.

    :copyright: (c) 2007-2012 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.portal.user import User
from inyoka.utils.flashing import flash
from inyoka.utils.html import escape
from inyoka.utils.sessions import set_session_info


class AuthMiddleware(object):

    def process_request(self, request):
        try:
            user_id = request.session['uid']
            user = User.objects.get(pk=user_id)
        except (User.DoesNotExist, KeyError):
            user = User.objects.get_anonymous_user()

        # check for bann/deletion
        if user.is_banned or user.is_deleted:
            if user.is_banned:
                flash((u'Du wurdest ausgeloggt, da der Benutzer „%s“ '
                       u'gerade gebannt wurde.' % escape(user.username)), False,
                       session=request.session)
            elif user.is_deleted:
                flash((u'Du wurdest ausgeloggt, da du dein Benutzerkonto „%s“ '
                       u'in der Zwischenzeit gelöscht hast.' % escape(user.username)), False,
                       session=request.session)

            request.session.pop('uid', None)
            user = User.objects.get_anonymous_user()

        request.user = user
        set_session_info(request)
