#-*- coding: utf-8 -*-
"""
    inyoka.middlewares.auth
    ~~~~~~~~~~~~~~~~~~~~~~~

    This replaces the django auth middleware.

    :copyright: (c) 2007-2023 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import uuid

from django.contrib import auth, messages
from django.utils.crypto import constant_time_compare
from django.utils.deprecation import MiddlewareMixin
from django.utils.html import escape
from django.utils.translation import gettext as _

from inyoka.portal.user import User
from inyoka.utils.sessions import set_session_info


class AuthMiddleware(MiddlewareMixin):

    def process_request(self, request):
        try:
            user_id = request.session[auth.SESSION_KEY]
            backend_path = request.session[auth.BACKEND_SESSION_KEY]
            backend = auth.load_backend(backend_path)
            user = backend.get_user(user_id)
            if user:
                session_hash = request.session.get(auth.HASH_SESSION_KEY)
                session_hash_verified = session_hash and constant_time_compare(
                    session_hash,
                    user.get_session_auth_hash()
                )
                if not session_hash_verified:
                    request.session.flush()
                    request.session['sid'] = str(uuid.uuid4())
                    request.session.new = True
                    user = None

            user = user or User.objects.get_anonymous_user()
        except (User.DoesNotExist, KeyError):
            user = User.objects.get_anonymous_user()

        # check for bann/deletion
        if user.is_banned or user.is_deleted:
            if user.is_banned:
                messages.error(request,
                    _('The user “%(name)s” was banned. Your session has ended.') % {
                        'name': escape(user.username)})
            elif user.is_deleted:
                messages.error(request,
                    _('The user “%(name)s” deleted his profile. '
                        'Your session has ended.') % {'name': escape(user.username)})

            request.session.pop('_auth_user_id', None)
            user = User.objects.get_anonymous_user()

        request.user = user
        set_session_info(request)
