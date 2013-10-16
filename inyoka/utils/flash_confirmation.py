# -*- coding: utf-8 -*-
"""
    inyoka.utils.flash_confirmation
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides a function decorator to flash a confirmation form upon
    deletion or revert views.

    :copyright: (c) 2008-2013 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _

from inyoka.utils.http import TemplateResponse
from inyoka.utils.urls import href
from inyoka.utils.decorators import patch_wrapper


def confirm_action(message=None, confirm=None, cancel=None):
    """Decorator to render and handle "Are you sure?" flash messages.

    Flashes a form to confirm an action via a POST request including CSRF
    protection using :func:`django.views.decorators.csrf.csrf_protect`
    """
    def wrapper(func):
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
