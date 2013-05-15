# -*- coding: utf-8 -*-
"""
    inyoka.portal.utils
    ~~~~~~~~~~~~~~~~~~~

    Utilities for the portal.

    :copyright: (c) 2007-2013 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import json
import calendar
from datetime import date, time

from django.http import HttpResponseRedirect
from django.contrib import messages
from django.db.models import Q
from django.utils.http import urlquote_plus

from inyoka.utils.urls import href
from inyoka.utils.decorators import patch_wrapper
from inyoka.utils.http import AccessDeniedResponse
from inyoka.utils.dates import date_time_to_datetime
from inyoka.utils.storage import storage


def check_login(message=None):
    """
    This function can be used as a decorator to check whether the user is
    logged in or not.  Also it's possible to send the user a message if
    he's logged out and needs to login.
    """
    def _wrapper(func):
        def decorator(*args, **kwargs):
            req = args[0]
            if req.user.is_authenticated():
                return func(*args, **kwargs)
            if message is not None:
                messages.info(req, message)
            args = {'next': 'http://%s%s' % (req.get_host(), req.path)}
            return HttpResponseRedirect(href('portal', 'login', **args))
        return patch_wrapper(decorator, func)
    return _wrapper


def require_permission(*perms):
    """
    This decorator checks whether the user has a special permission and
    raises 403 if he doesn't. If you pass more than one permission name,
    the view function is executed if the user has one of them.
    """
    def f1(func):
        def f2(request, *args, **kwargs):
            for perm in perms:
                if request.user.can(perm):
                    return func(request, *args, **kwargs)
            return abort_access_denied(request)
        return f2
    return f1


def simple_check_login(f):
    """
    This function can be used as a decorator to check whether the user is
    logged in or not.
    If he is, the decorated function is called normally, else the login page
    is shown without a response to the user.
    """
    def decorator(*args, **kwargs):
        req = args[0]
        if req.user.is_authenticated():
            return f(*args, **kwargs)
        args = {'next': 'http://%s%s' % (req.get_host(), req.path)}
        return HttpResponseRedirect(href('portal', 'login', **args))
    return patch_wrapper(decorator, f)


def abort_access_denied(request):
    """Abort with an access denied message or go to login."""
    if request.user.is_anonymous:
        args = {'next': 'http://%s%s' % (request.get_host(), request.path)}
        return HttpResponseRedirect(href('portal', 'login', **args))
    return AccessDeniedResponse()


def calendar_entries_for_month(year, month):
    """
    Return a list with all days in a month and the calendar entries grouped
    by day (also make an entry in the list if there is no event)
    """
    from inyoka.ikhaya.models import Event
    days = {}
    month_range = range(1, calendar.monthrange(year, month)[1] + 1)
    for i in month_range:
        days[i] = []
    start_date = date(year=year, month=month, day=month_range[0])
    end_date = date(year=year, month=month, day=month_range[-1])

    events = Event.objects.filter(
        Q(date__range=(start_date, end_date)) |
        Q(enddate__range=(start_date, end_date)), visible=True).all()

    for event in events:
        if event.date is not None:
            if event.date < start_date:
                delta = start_date - event.date
                base = start_date.day
            else:
                if event.enddate:
                    delta = event.enddate - event.date
                else:
                    delta = event.date - event.date
                base = event.date.day

            for day in range(delta.days + 1):
                if base + day in days:
                    days[base + day].append(event)
        else:
            days[event.date.day].append(event)
    return days


def google_calendarize(event):
    tfmt = '%Y%m%dT000000'

    start = date_time_to_datetime(event.date, event.time or time())
    dates = start.strftime(tfmt)
    if event.enddate:
        end = date_time_to_datetime(event.enddate, event.endtime or time())
        dates += '%2F' + end.strftime(tfmt)
    else:
        dates += '%2F' + start.strftime(tfmt)
    name = urlquote_plus(event.name)

    s = ('http://www.google.com/calendar/event?action=TEMPLATE&' +
         'text=' + name + '&' +
         'dates=' + dates + '&' +
         'sprop=website:ubuntuusers.de')

    if event.description:
        s += s + '&details=' + urlquote_plus(event.description)

    if event.location:
        s = s + '&location=' + urlquote_plus(event.simple_coordinates)

    return s + '&trp=false'


class UbuntuVersion(object):
    """
    This class holds a single Ubuntu version. Based on the settings for
    :py:attribute:`lts`, :py:attribute:`active`, :py:attribute:`current`,
    :py:attribute:`dev`, a different notification appears in the forum
    front-end while selecting the topic version.

    The attributes :py:attribute:`number` and :py:attribute:`name` have to be
    given.
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
        return u'%s (%s)' % (self.number, self.name)

    def __eq__(self, other):
        return self.number == other.number

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        s = map(int, self.number.split('.'))
        o = map(int, other.number.split('.'))
        #: Sort by major number and if they are the same, by minor version
        return s[0] < o[0] or s[0] == o[0] and s[1] < o[1]

    def __gt__(self, other):
        s = map(int, self.number.split('.'))
        o = map(int, other.number.split('.'))
        #: Sort by major number and if they are the same, by minor version
        return s[0] > o[0] or s[0] == o[0] and s[1] > o[1]

    def as_json(self):
        data = {
                'number': self.number,
                'name': self.name,
                'lts': self.lts,
                'acitve': self.active,
                'current': self.current,
                'dev': self.dev}
        return json.dumps(data)


class UbuntuVersionList(set):
    """
    This class holds a set of :py:class:`UbuntuVersion`. We are using a set to
    avoid duplicate entries. But accessing this class with all its version
    should be done by :py:var:`UBUNTU_VERSIONS`.
    """

    def __init__(self, data=u''):
        super(set, self).__init__()
        #: we need that try-except block to avoid failing `./manage syncdb`
        try:
            value = data or storage['distri_versions']
            jsonobjs = json.loads(value)
            for obj in jsonobjs:
                version = UbuntuVersion(**obj)
                self.add(version)
        except:
            pass


UBUNTU_VERSIONS = list(sorted(UbuntuVersionList()))
