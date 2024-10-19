"""
    inyoka.utils.http
    ~~~~~~~~~~~~~~~~~

    This module contains functions for http-related things like special
    responses etc.

    :copyright: (c) 2007-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, HttpResponse
from django.shortcuts import render

from inyoka.utils.decorators import patch_wrapper


def templated(template_name, status=None, modifier=None,
              content_type='text/html; charset=utf-8'):
    """
    This function can be used as a decorator to use a function's return value
    as template context if it's not a valid Response object.
    The first decorator argument should be the name of the template to use::

        @templated('mytemplate.html')
        def foo(req):
            return {
                'foo': 'bar'
            }

    `ObjectDoesNotExist` exceptions are caught and raised again as
    `PageNotFound`.
    """
    def decorator(f):
        def proxy(request, *args, **kwargs):
            try:
                rv = f(request, *args, **kwargs)
            except ObjectDoesNotExist:
                raise Http404()
            if isinstance(rv, HttpResponse):
                return rv
            elif rv is None:
                rv = {}
            if modifier is not None:
                modifier(request, rv)
            return render(request, template_name, rv, status=status, content_type=content_type)
        return patch_wrapper(proxy, f)
    return decorator


def does_not_exist_is_404(f):
    """For untemplated pages a `DoesNotExist` to `404`."""
    def proxy(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ObjectDoesNotExist:
            raise Http404()
    return patch_wrapper(proxy, f)


def global_not_found(request, err_message=None, exception=None):
    return render(request, 'errors/404.html', {
        'err_message': err_message,
    }, status=404)


def server_error(request, exception=None):
    return render(request, 'errors/500.html', {'request': request}, status=500)


def permission_denied_view(request, exception=None):
    return render(request, 'errors/403.html', {'request': request}, status=403)


def bad_request_view(request, exception=None):
    return render(request, 'errors/400.html', {'request': request}, status=400)

