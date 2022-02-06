# -*- coding: utf-8 -*-
"""
    inyoka.utils.dates
    ~~~~~~~~~~~~~~~~~~

    Various utilities for datetime handling.

    :copyright: (c) 2007-2022 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import re
from datetime import date, datetime, timedelta
from operator import attrgetter

import pytz
from django.contrib.humanize.templatetags.humanize import \
    naturalday as djnaturalday
from django.template import defaultfilters
from django.utils import datetime_safe, timezone

TIMEZONES = pytz.common_timezones


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


naturalday = lambda value, arg='DATE_FORMAT': djnaturalday(value, arg)
format_date = lambda value, arg='DATE_FORMAT': defaultfilters.date(value, arg)
format_datetime = lambda value, arg='DATETIME_FORMAT': defaultfilters.date(_localtime(value), arg)
format_time = lambda value, arg='TIME_FORMAT': defaultfilters.time(value, arg)
format_timetz = lambda value, arg='TIME_FORMAT': defaultfilters.time(_localtime(value), arg)


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
        'date': date(*k),
        'articles': items,
    } for k, items in days if items]


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
            args.extend(list(map(int, seconds.split('.'))))
        else:
            args.append(int(seconds))

    rv = datetime(*[_f for _f in args if _f])
    tz = groups[-1]
    if tz and tz != 'Z':
        args = list(map(int, tz[1:].split(':')))
        delta = timedelta(hours=args[0], minutes=args[1])
        if tz[0] == '+':
            rv += delta
        else:
            rv -= delta
    return rv


def format_iso8601(obj):
    """Format a datetime object for iso8601"""
    return datetime_safe.new_datetime(obj).strftime('%Y-%d-%mT%H:%M:%SZ')
