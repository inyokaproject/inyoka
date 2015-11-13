# -*- coding: utf-8 -*-
"""
    inyoka.utils.sessions
    ~~~~~~~~~~~~~~~~~~~~~

    Session related utility functions.


    :copyright: (c) 2007-2015 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime, timedelta
from time import time

from django.forms import ValidationError
from django.utils.translation import ugettext_lazy
from django.contrib.sessions.backends.cache import SessionStore as _SessionStore

from inyoka.portal.models import SessionInfo
from inyoka.utils.local import current_request
from inyoka.utils.storage import storage

SESSION_DELTA = 300


class SessionStore(_SessionStore):
    """
    Like the django cache session store but saves a second cache key for each
    session with a short time to live.
    """

    def save(self, *args, **kwargs):
        value = super(SessionStore, self).save(*args, **kwargs)
        if self.session_key is not None:
            self._cache.set('counter.{}'.format(self.cache_key), 0, SESSION_DELTA)
        return value


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
