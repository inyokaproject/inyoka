# -*- coding: utf-8 -*-
"""
    inyoka.utils.dates
    ~~~~~~~~~~~~~~~~~~

    Various utilities for datetime handling.

    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import re
import pytz
from operator import attrgetter
from datetime import date, datetime, timedelta
from django.utils import datetime_safe
from django.utils.dateformat import DateFormat
from django.utils.translation import get_language_from_request
from inyoka.utils.local import current_request


MONTHS = ['Januar', 'Februar', u'März', 'April', 'Mai', 'Juni',
          'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember']
WEEKDAYS = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag',
            'Samstag', 'Sonntag']
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
    } for key, entries in days if entries]


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


def format_timedelta(d, now=None, use_since=False, short=False):
    """
    Format a timedelta.  Currently this method only works with
    dates in the past.
    """
    chunks = (
        (60 * 60 * 24 * 365, ('m', 'Jahr', 'Jahren')),
        (60 * 60 * 24 * 30, ('m', 'Monat', 'Monaten')),
        (60 * 60 * 24 * 7, ('f', 'Woche', 'Wochen')),
        (60 * 60 * 24, ('m', 'Tag', 'Tagen')),
        (60 * 60, ('f', 'Stunde', 'Stunden')),
        (60, ('f', 'Minute', 'Minuten')),
        (1, ('f', 'Sekunde', 'Sekunden'))
    )
    if now is None:
        now = datetime.utcnow().replace(tzinfo=pytz.UTC)
    elif now.tzinfo is not None:
        now = d.astimezone(pytz.UTC)
    else:
        now = d.replace(tzinfo=pytz.UTC)
    if isinstance(d, date):
        d = datetime(d.year, d.month, d.day)
    if d.tzinfo is None:
        d = d.replace(tzinfo=pytz.UTC)
    else:
        d = d.astimezone(pytz.UTC)
    delta = now - d

    since = delta.days * 24 * 60 * 60 + delta.seconds
    if since <= 0:
        return 'gerade eben'

    for idx, (seconds, detail) in enumerate(chunks):
        count = since // seconds
        if count != 0:
            result = [(count, detail)]
            break

    if not short:
        if idx + 1 < len(chunks):
            seconds2, detail = chunks[idx + 1]
            count = (since - (seconds * count)) // seconds2
            if count != 0:
                result.append((count, detail))

    def format(num, genus, singular, plural):
        if not 0 < num <= 12:
            return '%d %s' % (num, plural)
        elif num == 1:
            return {
                'm':        'einem',
                'f':        'einer'
            }[genus] + ' ' + singular
        return ('zwei', 'drei', 'vier', u'fünf', 'sechs',
                'sieben', 'acht', 'neun', 'zehn', 'elf',
                u'zwölf')[num - 2] + ' ' + plural

    return (use_since and 'seit' or 'vor') + ' ' + \
           u' und '.join(format(a, *b) for a, b in result)


def timedelta_to_seconds(t):
    """
    Convert a datetime.timedelta to Seconds.
    """
    return t.days * 86400 + t.seconds


def natural_date(value, prefix=False, enforce_utc=False):
    """
    Format a value using dateformat but also use today, tomorrow and
    yesterday.  If a date object is given no timezone logic is applied,
    otherwise the usual timezone conversion rules apply.
    """
    if not isinstance(value, datetime):
        value = datetime(value.year, value.month, value.day)
        delta = datetime.utcnow() - value
    else:
        value = datetime_to_timezone(value, enforce_utc)
        delta = datetime.utcnow().replace(tzinfo=pytz.UTC) - value
    if -1 <= delta.days <= 1:
        return (u'morgen', u'heute', u'gestern')[delta.days + 1]
    return (prefix and 'am ' or '') + DateFormat(value).format('j. F Y')


def format_time(value, enforce_utc=False):
    """Format a datetime object for time."""
    value = datetime_to_timezone(value, enforce_utc)
    rv = DateFormat(value).format('H:i')
    if enforce_utc:
        rv += ' (UTC)'
    return rv


def format_datetime(value, enforce_utc=False):
    """Just format a datetime object."""
    value = datetime_to_timezone(value, enforce_utc)
    rv = DateFormat(value).format('j. F Y H:i')
    if enforce_utc:
        rv += ' (UTC)'
    return rv


def format_specific_datetime(value, alt=False, enforce_utc=False):
    """
    Use German grammar to format a datetime object for a
    specific datetime.
    """
    if not isinstance(value, datetime):
        value = datetime(value.year, value.month, value.day)

    delta = datetime.utcnow().replace(tzinfo=pytz.UTC).date() - \
            datetime_to_timezone(value, True).date()
    if -1 <= delta.days <= 1:
        string = (
            (u'von morgen ', u'morgen um '),
            (u'von heute ', u'heute um '),
            (u'von gestern ', 'gestern um ')
        )[delta.days + 1][bool(alt)]
    else:
        string = (alt and u'am %s um ' or 'vom %s um ') % \
            DateFormat(value).format('j. F Y')
    return string + format_time(value, enforce_utc) + ' Uhr'
