# -*- coding: utf-8 -*-
"""
    inyoka.middlewares.tz
    ~~~~~~~~~~~~~~~~~~~~~

    Middleware to set the current timezone for Django.

    :copyright: (c) 2013-2020 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.utils import timezone


class TimezoneMiddleware(object):
    def process_request(self, request):
        tz = request.session.get('django_timezone')
        if tz:
            timezone.activate(tz)
        else:
            timezone.deactivate()
