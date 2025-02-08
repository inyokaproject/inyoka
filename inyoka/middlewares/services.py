"""
    inyoka.middlewares.services
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Because of the same-origin policy we do not serve AJAX services as part
    of the normal, subdomain bound request dispatching.  This middleware
    dispatches AJAX requests on every subdomain to the modules that provide
    JSON callbacks.

    What it does is listening for "/?__service__=wiki.something" which
    dispatches to ``inyoka.wiki.services.dispatcher('something')``.


    :copyright: (c) 2007-2025 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import json
from typing import Final

from django.http import HttpResponse, HttpResponseBadRequest
from django.utils.cache import add_never_cache_headers
from django.utils.deprecation import MiddlewareMixin

JSON_CONTENTTYPE: Final[str] = 'application/json'
ALLOWED_APPS = ('portal', 'forum', 'ikhaya', 'wiki')


class ServiceMiddleware(MiddlewareMixin):

    def process_request(self, request):
        if request.path == '/' and '__service__' in request.GET:
            parts = request.GET['__service__'].split('.', 1)

            if len(parts) != 2:
                return HttpResponseBadRequest()

            app, action = parts

            if app not in ALLOWED_APPS:
                return HttpResponseBadRequest()

            try:
                call = __import__(f'inyoka.{ app }.services', None,
                                  None, ['dispatcher']).dispatcher
            except (ImportError, AttributeError):
                return HttpResponseBadRequest()
            else:
                response = call(request, action)

            if isinstance(response, HttpResponse):
                retval = response
            else:
                data = json.dumps(response)
                retval = HttpResponse(data, content_type=JSON_CONTENTTYPE)

            if getattr(call, '__never_cache__', False):
                add_never_cache_headers(response)

            return retval
