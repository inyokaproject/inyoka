#-*- coding: utf-8 -*-
"""
    inyoka.middlewares.auth
    ~~~~~~~~~~~~~~~~~~~~~~~

    This replaces the django auth middleware.

    :copyright: (c) 2007-2015 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.contrib import auth, messages
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.utils.html import escape
from django.utils.translation import ugettext as _

from inyoka.portal.user import User


class AuthMiddleware(AuthenticationMiddleware):
    """
    Link django.contrib.auth.middleware.AuthenticationMiddleware but checks
    that the user is not banned or deleted
    """

    def process_request(self, request):
        super(AuthMiddleware, self).process_request(request)

        # We use our own AnonymousUser.
        if isinstance(request.user, AnonymousUser):
            request.user = User.objects.get_anonymous_user()

        # check for bann/deletion
        if request.user.is_banned or request.user.is_deleted:
            if request.user.is_banned:
                messages.error(request,
                    _(u'The user “%(name)s” was banned. Your session has ended.') % {
                        'name': escape(request.user.username)})
            elif request.user.is_deleted:
                messages.error(request,
                    _(u'The user “%(name)s” deleted his profile. '
                        u'Your session has ended.') % {'name': escape(request.user.username)})

            request.session.flush()
            request.user = User.objects.get_anonymous_user()
