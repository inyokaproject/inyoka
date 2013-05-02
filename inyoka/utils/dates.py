# -*- coding: utf-8 -*-
"""
    inyoka.utils.dates
    ~~~~~~~~~~~~~~~~~~

    Various utilities for datetime handling.

    :copyright: (c) 2007-2013 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import re
import pytz
from operator import attrgetter
from datetime import date, datetime, timedelta, time
from django.contrib.humanize.templatetags.humanize import naturalday
from django.utils import datetime_safe
from django.utils.dateformat import DateFormat
from django.utils.translation import get_language_from_request, ugettext as _
from inyoka.utils.local import current_request


TIMEZONES = pytz.common_timezones
DEFAULT_TIMEZONE = pytz.timezone('Europe/Berlin')


_iso8601_re = re.compile(
    # date
    r'(\d{4})(?:-?(\d{2})(?:-?(\d{2}))?)?'
    # time
    r'(?:T(\d{2}):(\d{2})(?::(\d{2}(?:\.\d+)?))?(Z?|[+-]\d{2}:\d{2})?)?$'
)


def group_by_day(entries, date_func=attrgetter('pub_date'),
                 enforce_utc=False):
    """
    Group a list of entries by the date but in the users's timezone
    (or UTC if enforce_utc is set to `True`).  Per default the pub_date
    Attribute is used.  If this is not desired a different `date_func`
    can be provided.  It's important that the list is already sorted
    by date otherwise the behavior is undefined.
    """
    days = []
    days_found = set()
    if enforce_utc:
        tzinfo = pytz.UTC
    else:
        tzinfo = get_user_timezone()
    for entry in entries:
        d = date_func(entry)
        if d.tzinfo is None:
            d = d.replace(tzinfo=pytz.UTC)
        d = d.astimezone(tzinfo)
        key = (d.year, d.month, d.day)
        if key not in days_found:
            days.append((key, []))
            days_found.add(key)
        days[-1][1].append(entry)
    return [{
        'date':     date(*key),
        'articles': entries
    } for key, items in days if items]


def get_user_timezone():
    """
    Return the timezone of the current user or UTC if there is no user
    available (eg: no web request).
    """
    try:
        user = getattr(current_request, 'user', None)
    except RuntimeError:
        user = None
    try:
        return pytz.timezone(user.settings.get('timezone', ''))
    except:
        return DEFAULT_TIMEZONE


def find_best_timezone(request):
    """Return the best timezone match based on browser language.

    This is not the best way to do that but good enough for the moment.
    """
    timezone = DEFAULT_TIMEZONE
    language_header = request.META.get('HTTP_ACCEPT_LANGUAGES')
    if language_header:
        try:
            timezones = pytz.country_timezones(get_language_from_request(request))
            if not timezones:
                raise LookupError()
        except LookupError:
            pass
        else:
            timezone = timezones[0]
    return timezone


def datetime_to_timezone(dt, enforce_utc=False):
    """
    Convert a datetime object to the user's timezone or UTC if the
    user is not available or `enforce_utc` was set to `True` to enforce
    UTC.  If the object is `None` it's returned unchanged.
    """
    if dt is None:
        return None
    if enforce_utc:
        tz = pytz.UTC
    else:
        tz = get_user_timezone()
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=pytz.UTC)
    return datetime_safe.new_datetime(dt.astimezone(tz))


def datetime_to_naive_utc(dt):
    """
    Convert a datetime object with a timezone information into a datetime
    object without timezone information in UTC timezone.  If the object
    did not contain a timezone information it's returned unchainged.
    """
    if dt.tzinfo is None:
        return dt
    return datetime_safe.new_datetime(dt.astimezone(pytz.UTC).replace(tzinfo=None))

date_time_to_datetime = datetime.combine


def parse_iso8601(value):
    """
    Parse an iso8601 date into a datetime object.
    The timezone is normalized to UTC, we always use UTC objects
    internally.
    """
    m = _iso8601_re.match(value)
    if m is None:
        raise ValueError('not a valid iso8601 date value')

    groups = m.groups()
    args = []
    for group in groups[:-2]:
        if group is not None:
            group = int(group)
        args.append(group)
    seconds = groups[-2]
    if seconds is not None:
        if '.' in seconds:
            args.extend(map(int, seconds.split('.')))
        else:
            args.append(int(seconds))

    rv = datetime(*filter(None, args))
    tz = groups[-1]
    if tz and tz != 'Z':
        args = map(int, tz[1:].split(':'))
        delta = timedelta(hours=args[0], minutes=args[1])
        if tz[0] == '+':
            rv += delta
        else:
            rv -= delta
    return rv


def format_iso8601(obj):
    """Format a datetime object for iso8601"""
    return datetime_safe.new_datetime(obj).strftime('%Y-%d-%mT%H:%M:%SZ')


def timedelta_to_seconds(t):
    """
    Convert a datetime.timedelta to Seconds.
    """
    return t.days * 86400 + t.seconds


def format_time(value, day=None, daytime=False):
    """Format a datetime object for time."""
    if isinstance(value, time) and not day:
        value = datetime.combine(datetime.utcnow().date(), value)
    elif day:
        value = datetime.combine(day, value)
    value = datetime_to_timezone(value)

    # WTF is daytime doing?!
    format = 'H:i a' if daytime else 'H:i'
    return DateFormat(value).format(format)


def format_datetime(value):
    """Just format a datetime object."""
    value = datetime_to_timezone(value)
    rv = DateFormat(value).format('j. F Y H:i')
    return rv


def format_specific_datetime(value):
    """
    Use German grammar to format a datetime object for a
    specific datetime.
    """
    if not isinstance(value, datetime):
        value = datetime(value.year, value.month, value.day)

    return _(u'%(date)s at %(time)s') % {
        'date': naturalday(value),
        'time': format_time(value, daytime=True)}
