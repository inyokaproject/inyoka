# -*- coding: utf-8 -*-
"""
    inyoka.middlewares.common
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides a middleware that sets the url conf for the current
    request depending on the site we are working on and does some more common
    stuff like session updating.

    This middleware replaces the common middleware.

    For development purposes we also set up virtual url dispatching modules for
    static and media.

    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import re
from django.conf import settings
from django.middleware.common import CommonMiddleware

from django_hosts.middleware import HostsMiddleware
from django_mobile.middleware import \
    MobileDetectionMiddleware as BaseMobileDetectionMiddleware

from inyoka import INYOKA_REVISION
from inyoka.utils.flashing import has_flashed_messages
from inyoka.utils.local import local, _request_cache, local_manager
from inyoka.utils.timer import StopWatch
from inyoka.utils.logger import logger


re_htmlmime = re.compile(r'^text/x?html')


class CommonServicesMiddleware(HostsMiddleware, CommonMiddleware):
    """Hook in as first middleware for common tasks."""

    def process_request(self, request):
        # populate the request
        local.request = request
        # create local cache object if it does not exist
        # (so that our cache is not overwriting it every time...)
        try:
            _request_cache._get_current_object()
        except RuntimeError:
            local.cache = {}

        # Start time tracker
        request.watch = StopWatch()
        request.watch.start()

        # IMPORTANT: Since we run some setupcode (mainly locals), this middleware
        # needs to be the first one, hence we manually dispatch to HostsMiddleware
        response = HostsMiddleware.process_request(self, request)
        if response:
            return response

        host = request.get_host()
        request.subdomain = host[:-len(settings.BASE_DOMAIN_NAME)].rstrip('.')

        return CommonMiddleware.process_request(self, request)

    def process_response(self, request, response):
        """
        Hook our X-Powered header in (and an easteregg header).  And clean up
        the werkzeug local.
        """
        response = CommonMiddleware.process_response(self, request, response)
        powered_by = 'Inyoka'
        if INYOKA_REVISION:
            powered_by += '/rev-%s' % INYOKA_REVISION
        response['X-Powered-By'] = powered_by
        response['X-Philosophy'] = 'Don\'t be hasty, open a ticket, get some holiday and let us relax. We\'re on it.'

        # update the cache control
        if hasattr(request, 'user') and request.user.is_authenticated \
           or has_flashed_messages():
            response['Cache-Control'] = 'no-cache'

        path = request.path
        exclude = (any(x in path for x in ('.js', '.css'))
                   or '__service__' in request.GET
                   or 'Content-Disposition' in response
                   or 'html' in response['Content-Type'])
        if settings.DEBUG and not exclude:
            response['Access-Control-Allow-Origin'] = '*'

        # warn of slow requests
        if int(request.watch.duration) > 5:
            logger.warning(u'Slow Request', extra={
                'request': request, 'url': request.build_absolute_uri()
            })


        local_manager.cleanup()

        return response


class MobileDetectionMiddleware(BaseMobileDetectionMiddleware):
    user_agents_test_search = "(?:up.browser|up.link|mmp|symbian|smartphone|midp|wap|phone|windows ce|pda|mobile|mini|palm|netfront|fennec)"


# import all application modules so that we get bootstrapping
# code executed. (in the apps __init__.py file)
_app = None
for _app in settings.INSTALLED_APPS:
    __import__(_app)
del _app
