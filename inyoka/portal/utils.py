"""
    inyoka.portal.utils
    ~~~~~~~~~~~~~~~~~~~

    Utilities for the portal.

    :copyright: (c) 2007-2025 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import calendar
import json
from datetime import date
from urllib.parse import quote_plus

from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseRedirect

from inyoka.utils.storage import storage
from inyoka.utils.urls import href


def abort_access_denied(request):
    """Abort with access denied message or redirect to login-page."""
    if request.user.is_anonymous:
        args = {'next': '//%s%s' % (request.get_host(), request.path)}
        return HttpResponseRedirect(href('portal', 'login', **args))

    raise PermissionDenied


def calendar_entries_for_month(year, month):
    """
    Return a list with all days in a month and the calendar entries grouped
    by day (also make an entry in the list if there is no event)
    """
    from inyoka.ikhaya.models import Event
    days = {}
    month_range = list(range(1, calendar.monthrange(year, month)[1] + 1))
    for i in month_range:
        days[i] = []
    start_date = date(year=year, month=month, day=month_range[0])

    events = Event.objects.filter(Q(start__year=year, start__month=month) | Q(end__year=year, end__month=month), visible=True)

    for event in events:
        if event.start.date() < start_date:
            delta = event.end.date() - start_date
            base = start_date.day
        else:
            delta = event.end.date() - event.start.date()
            base = event.start.date().day

        for day in range(delta.days + 1):
            if base + day in days:
                days[base + day].append(event)

    return days


def google_calendarize(event):
    tfmt = '%Y%m%dT000000'

    dates = event.start.strftime(tfmt)
    dates += '%2F' + event.end.strftime(tfmt)
    name = quote_plus(event.name)

    s = ('https://www.google.com/calendar/event?action=TEMPLATE&' +
         'text=' + name + '&' +
         'dates=' + dates + '&' +
         'sprop=website:ubuntuusers.de')

    if event.description:
        s += s + '&details=' + quote_plus(event.description)

    if event.location:
        s = s + '&location=' + quote_plus(event.simple_coordinates)

    return s + '&trp=false'


class UbuntuVersion:
    """
    This class holds a single Ubuntu version. Based on the settings for
    :py:attr:`lts`, :py:attr:`active`, :py:attr:`current`, :py:attr:`dev`, a
    different notification appears in the forum front-end while selecting the
    topic version.

    The attributes :py:attr:`number` and :py:attr:`name` have to be given.
    """

    def __init__(self, number, name, lts=False, active=False,
                 current=False, dev=False):
        self.number = number
        self.name = name
        self.lts = lts
        self.active = active
        self.current = current
        self.dev = dev
        self.link = href('wiki', name)

    def is_active(self):
        """
        This function allows a simple access where the version is active, or
        will be active, or if its support range is outdated.
        """
        return self.active or self.current or self.dev

    def __str__(self):
        return '%s (%s)' % (self.number, self.name)

    def __eq__(self, other):
        return self.number == other.number

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        s = list(map(int, self.number.split('.')))
        o = list(map(int, other.number.split('.')))
        #: Sort by major number and if they are the same, by minor version
        return s[0] < o[0] or s[0] == o[0] and s[1] < o[1]

    def __gt__(self, other):
        s = list(map(int, self.number.split('.')))
        o = list(map(int, other.number.split('.')))
        #: Sort by major number and if they are the same, by minor version
        return s[0] > o[0] or s[0] == o[0] and s[1] > o[1]

    def __hash__(self):
        return hash(self.number) ^ hash(self.name)

    def as_json(self):
        data = {
            'number': self.number,
            'name': self.name,
            'lts': self.lts,
            'active': self.active,
            'current': self.current,
            'dev': self.dev}
        return json.dumps(data)


def get_ubuntu_versions():
    #: we need that try-except block to avoid failing `./manage syncdb`
    sid = transaction.savepoint()
    versions = set()
    try:
        jsonobjs = json.loads(storage['distri_versions'])
        for obj in jsonobjs:
            version = UbuntuVersion(**obj)
            versions.add(version)
    except Exception:
        transaction.savepoint_rollback(sid)
    else:
        transaction.savepoint_commit(sid)
    return sorted(versions)
