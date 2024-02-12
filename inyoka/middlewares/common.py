"""
    inyoka.middlewares.common
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides a middleware that sets the url conf for the current
    request depending on the site we are working on and does some more common
    stuff like session updating.

    This middleware replaces the common middleware.

    For development purposes we also set up virtual url dispatching modules for
    static and media.

    :copyright: (c) 2007-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse
from django.middleware.common import CommonMiddleware
from django.utils.functional import cached_property
from django_hosts.middleware import HostsRequestMiddleware

from inyoka.utils.local import local, local_manager
from inyoka.utils.logger import logger
from inyoka.utils.timer import StopWatch


class CommonServicesMiddleware(HostsRequestMiddleware, CommonMiddleware):
    """Hook in as first middleware for common tasks."""

    @cached_property
    def table_control_characters(self):
        """
        Returns a translation table which removes all control characters not allowed in XML/HTML.
        Use it with `str.translate`.

        The characters can be also described by the regex r'[\x00-\x08\x0B-\x0C\x0E-\x1F]'.
        However, the regex performed slower in a little benchmark comparison.
        """
        table = {0x0B: None, 0x0C: None}
        for i in range(0x0, 0x08 + 1):
            table[i] = None

        for i in range(0x0E, 0x1F + 1):
            table[i] = None

        return table

    def process_request(self, request):
        # populate the request
        local.request = request

        # Start time tracker
        request.watch = StopWatch()
        request.watch.start()

        # reject URLs with NUL byte.
        # If those are passed to the ORM with postgres, an exception is raised
        # It's also mentioned in https://datatracker.ietf.org/doc/html/rfc3986#section-7.3
        if '\x00' in request.path:
            return HttpResponse(content='The URL contained NUL characters', status=400, content_type='text/plain')

        # remove control characters in all POST fields
        # Thus, these will not slip into the DB and will not be displayed to users in HTML/XML
        # request.POST does not contain file uploads
        if request.method == "POST":
            new_post = request.POST.copy()
            for key, value_list in new_post.lists():
                new_post.setlist(key, [v.translate(self.table_control_characters) for v in value_list])
            new_post._mutable = False
            request.POST = new_post

        # IMPORTANT: Since we run some setup-code (mainly locals), this middleware
        # needs to be the first one, hence we manually dispatch to HostsMiddleware
        response = HostsRequestMiddleware.process_request(self, request)
        if response is not None:
            return response

        host = request.get_host()
        request.subdomain = host[:-len(settings.BASE_DOMAIN_NAME)].rstrip('.')

        return CommonMiddleware.process_request(self, request)

    def process_response(self, request, response):
        response = CommonMiddleware.process_response(self, request, response)

        # update the cache control
        if hasattr(request, 'user') and request.user.is_authenticated \
           or len(messages.get_messages(request)):
            response['Cache-Control'] = 'no-cache'

        path = request.path
        if (path.endswith(('.less', '.woff', '.woff2', '.eot', '.ttf', '.otf'))
                and settings.DEBUG):
            response['Access-Control-Allow-Origin'] = '*'

        request.watch.stop()
        logger_extras = {
            'request': request,
            'url': request.build_absolute_uri(),
            'duration': request.watch.duration,
        }
        duration = request.watch.duration
        if duration < 5.0:
            logger.debug('Request Duration', extra=logger_extras)
        if 5.0 <= duration < 10.0:
            logger.info('Slow Request', extra=logger_extras)
        if duration >= 10.0:
            logger.warn('Very Slow Request', extra=logger_extras)

        local_manager.cleanup()

        return response
