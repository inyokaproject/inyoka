# -*- coding: utf-8 -*-
from django.http import HttpResponseRedirect
from django.utils.html import escape
from django.utils.http import urlencode
from django.utils.translation import ugettext as _

from django.contrib import messages

from inyoka.portal.user import User


def collect_registration_info(request, details, user=None, *args, **kwargs):
    if user is None and not request.session.get('social_auth_data'):
        d = {'username': details.get('username', ''),
             'email': details.get('email', '')}
        return HttpResponseRedirect('/register/external/?' + urlencode(d))


def get_username(request, user=None, *args, **kwargs):
    if user is not None:
        return {'username': user.username}
    return request.session.pop('social_auth_data')


def create_user(details, username, email=None, user=None, *args, **kwargs):
    if user:
        return {'user': user}
    if not username or not email:
        return None

    user = User.objects.register_user(username, email, None)
    messages.success(kwargs['request'],
        _(u'The username “%(username)s” was successfully registered. '
          u'An email with the activation key was sent to '
          u'“%(email)s”.') % {
              'username': escape(user.username),
              'email': escape(user.email)})

    return {
        'user': user,
        'is_new': True
    }

def clear_session(request, *args, **kwargs):
    request.session.pop('social_auth_data', None)
    request.session.pop('partial_pipeline', None)
    request.session.pop('openid', None)
    request.session.modified = True
