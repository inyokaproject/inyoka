#-*- coding: utf-8 -*-
"""
    inyoka.middlewares.auth
    ~~~~~~~~~~~~~~~~~~~~~~~

    This replaces the django auth middleware.

    :copyright: (c) 2007-2012 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from django.contrib import messages

from django.utils.html import escape
from django.utils.translation import ugettext as _

from inyoka.portal.user import User
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
                messages.error(request,
                    _(u'The user “%(name)s” was banned. Your session has ended.') % {
                    'name': escape(user.username)})
            elif user.is_deleted:
                messages.error(request,
                    _(u'The user “%(name)s” deleted his profile. '
                        u'Your session has ended.') % {'name': escape(user.username))

            request.session.pop('uid', None)
            user = User.objects.get_anonymous_user()

        request.user = user
        set_session_info(request)
