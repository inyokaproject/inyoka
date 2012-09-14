# -*- coding: utf-8 -*-
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_protect

from inyoka.utils.decorators import patch_wrapper
from inyoka.utils.http import HttpResponseRedirect, TemplateResponse
from inyoka.utils.urls import href


def confirm_action(message=None, confirm=None, cancel=None):
    """Decorator to render and handle "Are you sure?" flash messages.

    Flashes a form to confirm an action via a POST request including CSRF
    protection using :func:`django.views.decorators.csrf.csrf_protect`
    """
    def wrapper(func):
        @csrf_protect
        def decorator(request, *args, **kwargs):
            if request.method == 'POST':
                if 'confirm' in request.POST:
                    return func(request, *args, **kwargs)
                return HttpResponseRedirect(href('portal'))
            else:
                msg = message or _('Are you sure?')
                confirm_label = confirm or _('Yes')
                cancel_label = cancel or _('No')

                return TemplateResponse('confirm_action.html', {
                    'action_url': request.build_absolute_uri(),
                    'message': msg,
                    'confirm_label': confirm_label,
                    'cancel_label': cancel_label,
                    }, content_type='text/html; charset=utf-8')
        return patch_wrapper(decorator, func)
    return wrapper
