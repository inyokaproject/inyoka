# -*- coding: utf-8 -*-
"""
    inyoka.utils.dates
    ~~~~~~~~~~~~~~~~~~

    Various utilities for datetime handling.

    :copyright: (c) 2007-2013 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import re
from operator import attrgetter
from datetime import date, time, datetime, timedelta

from django.contrib.humanize.templatetags.humanize import naturalday as djnaturalday
from django.template import defaultfilters
from django.utils import timezone, datetime_safe
from django.utils.translation import get_language_from_request
import pytz

from inyoka.utils.local import current_request


TIMEZONES = pytz.common_timezones
DEFAULT_TIMEZONE = pytz.timezone('Europe/Berlin')


_iso8601_re = re.compile(
    # date
    r'(\d{4})(?:-?(\d{2})(?:-?(\d{2}))?)?'
    # time
    r'(?:T(\d{2}):(\d{2})(?::(\d{2}(?:\.\d+)?))?(Z?|[+-]\d{2}:\d{2})?)?$'
)

def _localtime(val):
    if val.tzinfo is None:
        val = timezone.make_aware(val, pytz.UTC)
    return timezone.localtime(val)

naturalday = lambda value, arg='DATE_FORMAT': djnaturalday(_localtime(value), arg)
format_date = lambda value, arg='DATE_FORMAT': defaultfilters.date(_localtime(value), arg)
format_datetime = lambda value, arg='DATETIME_FORMAT': defaultfilters.date(_localtime(value), arg)
format_time = lambda value, arg='TIME_FORMAT': defaultfilters.time(_localtime(value), arg)


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
        tzinfo = timezone.get_current_timezone()
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
        'date': date(*key),
        'articles': items,
    } for key, items in days if items]


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
        tz = timezone.get_current_timezone()
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=pytz.UTC)
    return datetime_safe.new_datetime(dt.astimezone(tz))


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
