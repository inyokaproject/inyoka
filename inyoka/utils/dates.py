"""
    inyoka.utils.dates
    ~~~~~~~~~~~~~~~~~~

    Various utilities for datetime handling.

    :copyright: (c) 2007-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import zoneinfo
from datetime import date
from datetime import timezone as py_timezone
from functools import lru_cache
from operator import attrgetter

from django.contrib.humanize.templatetags.humanize import \
    naturalday as djnaturalday
from django.template import defaultfilters
from django.utils import timezone
from django.utils.timezone import is_naive


@lru_cache(maxsize=None)
def get_timezone_list():
    # TODO https://adamj.eu/tech/2021/05/06/how-to-list-all-timezones-in-python/#deprecated-names
    return zoneinfo.available_timezones()


TIMEZONES = get_timezone_list()


def _localtime(val):
    if is_naive(val):
        val = timezone.make_aware(val, py_timezone.utc)
    return timezone.localtime(val)


naturalday = lambda value, arg='DATE_FORMAT': djnaturalday(value, arg)
format_date = lambda value, arg='DATE_FORMAT': defaultfilters.date(value, arg)
format_datetime = lambda value, arg='DATETIME_FORMAT': defaultfilters.date(_localtime(value), arg)
format_time = lambda value, arg='TIME_FORMAT': defaultfilters.time(value, arg)
format_timetz = lambda value, arg='TIME_FORMAT': defaultfilters.time(_localtime(value), arg)


def group_by_day(entries, date_func=attrgetter('pub_date'),
                 enforce_utc=False):
    """
    Group a list of entries by the date but in the users' timezone
    (or UTC if enforce_utc is set to `True`).  Per default the pub_date
    Attribute is used.  If this is not desired a different `date_func`
    can be provided.  It's important that the list is already sorted
    by date otherwise the behavior is undefined.
    """
    days = []
    days_found = set()

    if enforce_utc:
        tzinfo = py_timezone.utc
    else:
        tzinfo = timezone.get_current_timezone()

    for entry in entries:
        d = date_func(entry)
        if is_naive(d):
            d = d.replace(tzinfo=py_timezone.utc)
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
        tz = py_timezone.utc
    else:
        tz = timezone.get_current_timezone()

    if is_naive(dt):
        dt = dt.replace(tzinfo=py_timezone.utc)

    return dt.astimezone(tz)
