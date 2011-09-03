# -*- coding: utf-8 -*-
from inyoka.utils.decorators import patch_wrapper
from inyoka.utils.http import HttpResponseRedirect, TemplateResponse
from inyoka.utils.urls import href

def confirm_action(message=None, confirm=None, cancel=None):
    """Decorator to render and handle "Are you sure?" flash messages.

    Flashes a form to confirm an action via a POST request. Returns `True` if
    the action was confirmed successfully.

    """
    def wrapper(func):
        def decorator(request, *args, **kwargs):
            if request.method == 'POST':
                if 'cancel' in request.POST:
                    return HttpResponseRedirect(href('portal'))
                return func(request, *args, **kwargs)
            else:
                msg = message or 'Bist du sicher?'
                confirm_label = confirm or 'Ja'
                cancel_label = cancel or 'Nein'

                return TemplateResponse('confirm_action.html', {
                    'action_url': request.build_absolute_uri(),
                    'message': msg,
                    'confirm_label': confirm_label,
                    'cancel_label': cancel_label,
                    }, content_type='text/html; charset=utf-8')
        return patch_wrapper(decorator, func)
    return wrapper
