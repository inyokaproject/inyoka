# -*- coding: utf-8 -*-
"""
    inyoka.utils.flash_confirmation
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides a function decorator to flash a confirmation form upon
    deletion or revert views.

    :copyright: (c) 2008-2016 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _

from inyoka.utils.decorators import patch_wrapper
from inyoka.utils.http import TemplateResponse
from inyoka.utils.urls import href
from inyoka.utils.templating import render_template


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


class ConfirmActionMixin(object):
    """ConfirmActionMixin inject a flash message into the view."""
    confirm_message = None
    confirm_label = _(u'Confirm')
    success_message = _(u'Success')
    success_url = None
    cancel_label = _(u'Cancel')
    cancel_message = _(u'Aborted')
    cancel_url = None

    def get_context_data(self, **context):
        """Inject the flash confirmation form into request."""
        messages.info(self.request,
                      render_template('confirm_action_flash.html',
                                      {
                                          'message': self.confirm_message,
                                          'confirm_label': self.confirm_label,
                                          'cancel_label': self.cancel_label,
                                      },
                                      flash=True))
        return super(ConfirmActionMixin, self).get_context_data(**context)

    def post(self, request, pk):
        """Run the confirm_action method, when the injected form was submitted."""
        self.object = self.get_object()

        if 'confirm' in request.POST:
            self.confirm_action()
            messages.success(request, self.success_message)
            return HttpResponseRedirect(self.get_success_url())

        else:
            messages.info(request, self.cancel_message)
            return HttpResponseRedirect(self.get_cancel_url())

    def get_success_url(self):
        """Return the URL to redirect to in case of confirmed action."""
        if self.success_url is not None:
            return self.success_url
        else:
            return self.object.get_absolute_url()

    def get_cancel_url(self):
        """Return the URL to redirect to in case of aborted action."""
        if self.cancel_url is not None:
            return self.cancel_url
        else:
            return self.object.get_absolute_url()
