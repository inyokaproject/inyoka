#-*- coding: utf-8 -*-
"""
    inyoka.middlewares.auth
    ~~~~~~~~~~~~~~~~~~~~~~~

    This replaces the django auth middleware.

    :copyright: (c) 2007-2013 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from django.contrib import auth, messages
from django.utils.html import escape
from django.utils.translation import ugettext as _

from inyoka.portal.user import User
from inyoka.utils.sessions import set_session_info


class AuthMiddleware(object):

    def process_request(self, request):
        try:
            user_id = request.session[auth.SESSION_KEY]
            backend_path = request.session[auth.BACKEND_SESSION_KEY]
            backend = auth.load_backend(backend_path)
            user = backend.get_user(user_id) or User.objects.get_anonymous_user()
        except (User.DoesNotExist, KeyError):
            user = User.objects.get_anonymous_user()

        # check for bann/deletion
        if user.is_banned or user.is_deleted:
            if user.is_banned:
                messages.error(request,
                    _(u'The user “%(name)s” was banned. Your session has ended.') % {
                        'name': escape(user.username)})
            elif user.is_deleted:
                messages.error(request,
                    _(u'The user “%(name)s” deleted his profile. '
                        u'Your session has ended.') % {'name': escape(user.username)})

            request.session.pop('_auth_user_id', None)
            user = User.objects.get_anonymous_user()

        request.user = user
        set_session_info(request)
