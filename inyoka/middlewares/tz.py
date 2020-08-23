# -*- coding: utf-8 -*-
"""
    inyoka.middlewares.tz
    ~~~~~~~~~~~~~~~~~~~~~

    Middleware to set the current timezone for Django.

    :copyright: (c) 2013-2020 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.utils import timezone


class TimezoneMiddleware:
    def __init__(self, get_response):
        """One-time configuration and initialization."""
        self.get_response = get_response

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        tz = request.session.get('django_timezone')
        if tz:
            timezone.activate(tz)
        else:
            timezone.deactivate()

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response
