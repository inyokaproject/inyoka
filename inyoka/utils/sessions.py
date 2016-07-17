# -*- coding: utf-8 -*-
"""
    inyoka.utils.sessions
    ~~~~~~~~~~~~~~~~~~~~~

    Session related utility functions.


    :copyright: (c) 2007-2016 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime, timedelta
from time import time

from django.forms import ValidationError
from django.utils.translation import ugettext_lazy

from inyoka.portal.models import SessionInfo
from inyoka.utils.local import current_request
from inyoka.utils.storage import storage
from inyoka.utils.urls import url_for

SESSION_DELTA = 300


def set_session_info(request):
    """Set the session info."""

    # Prevent extra queries for markup.css and jsi18n since they are loaded
    # with every request, in development this also prevents extra queries for
    # static files. In production these files are served by another server.
    if request.path in ('/markup.css/', '/jsi18n/') or request.subdomain in ('static', 'media'):
        return

    # if the session is new we don't add an entry.  It could be that
    # the user has no cookie support and that would fill our session
    # table with dozens of entries
    if request.session.new:
        return

    if request.user.is_authenticated() and not request.user.settings.get('hide_profile', False):
        key = 'user:%s' % request.user.id
        user_type = 'user'
        if request.user.has_perm('ikhaya.view_unpublished_article'):
            user_type = 'team'
        args = {
            'subject_text': request.user.username,
            'subject_type': user_type,
            'subject_link': url_for(request.user)
        }
    else:
        key = request.session['sid']
        args = {
            'subject_text': None,
            'subject_type': 'anonymous',
            'subject_link': None
        }

    args.update({
        'last_change': datetime.utcnow(),
    })

    session_info, created = SessionInfo.objects.get_or_create(key=key, defaults=args)
    if not created:
        SessionInfo.objects.filter(key=key).update(**args)


class SurgeProtectionMixin(object):
    """
    Mixin for forms to override the `clean()` method to perform an additional
    surge protection.  Give this method a higher MRO than the form baseclass!
    """

    surge_protection_timeout = 15
    surge_protection_message = ugettext_lazy(
        u'You cannot send data that fast in a row. '
        u'Please wait a bit until you submit the form again.'
    )
    surge_protection_identifier = None

    def clean(self):
        # only perform surge protection tests if the form is valid up
        # to that point.  This is important because otherwise form
        # errors would trigger the surge protection!
        if self.surge_protection_timeout is not None and self.is_valid():
            identifier = self.get_surge_protection_identifier()
            session = current_request.session
            session.setdefault('sp', {})
            if session['sp'].get(identifier, 0) >= time():
                raise ValidationError(self.surge_protection_message)
            session['sp'][identifier] = time() + self.surge_protection_timeout
        return super(SurgeProtectionMixin, self).clean()

    def get_surge_protection_identifier(self):
        return self.surge_protection_identifier or \
            (self.__class__.__module__ + '.' + self.__class__.__name__)


def get_user_record(values=None):
    """
    Get a tuple for the user record in the format ``(number, timestamp)``
    where number is an integer with the number of online users and
    timestamp a datetime object.
    """
    if values is None:
        values = storage.get_many(('session_record', 'session_record_time'))
    record, timestamp = (int(values.get('session_record', 1) or 1),
                         values.get('session_record_time', 0))
    if timestamp is None:
        timestamp = datetime.utcnow()
    else:
        timestamp = datetime.fromtimestamp(int(timestamp))
    return record, timestamp


def get_sessions(order_by='-last_change'):
    """Get a simple list of active sessions for the portal index."""
    delta = datetime.utcnow() - timedelta(seconds=SESSION_DELTA)
    sessions = []
    for item in SessionInfo.objects.filter(last_change__gt=delta) \
                                   .order_by(order_by):
        sessions.append({
            'anonymous': item.subject_text is None,
            'text': item.subject_text,
            'type': item.subject_type,
            'link': item.subject_link,
            'last_change': item.last_change,
        })

    anonymous = sum(x['anonymous'] for x in sessions)
    return {
        'anonymous': anonymous,
        'registered': len(sessions) - anonymous,
        'all': len(sessions),
        'sessions': sessions,
        'registered_sessions': [s for s in sessions if not s['anonymous']]
    }


def make_permanent(request):
    """Make this session a permanent one."""
    request.session['_perm'] = True


def is_permanent(request):
    """Check if the session is permanent."""
    return request.session.get('_perm')
