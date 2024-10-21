"""
    inyoka.utils.flash_confirmation
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides a function decorator to flash a confirmation form upon
    deletion or revert views.

    :copyright: (c) 2008-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.translation import gettext as _

from inyoka.forum.models import PostRevision
from inyoka.utils.decorators import patch_wrapper
from inyoka.utils.urls import href


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
                if 'post_id' in kwargs:
                    cancel_url = href('forum', 'post', kwargs['post_id'])
                elif 'topic_slug' in kwargs:
                    if 'page' in kwargs:
                        cancel_url = href('forum', 'topic',
                                          kwargs['topic_slug'], kwargs['page'])
                    else:
                        cancel_url = href('forum', 'topic',
                                          kwargs['topic_slug'])
                elif 'rev_id' in kwargs:
                    post = PostRevision.objects.get(id=kwargs['rev_id']).post
                    cancel_url = post.get_absolute_url()
                else:
                    cancel_url = href('portal')
                return HttpResponseRedirect(cancel_url)
            else:
                msg = message or _('Are you sure?')
                confirm_label = confirm or _('Yes')
                cancel_label = cancel or _('No')

                return render(request, 'confirm_action.html', {
                    'action_url': request.build_absolute_uri(),
                    'message': msg,
                    'confirm_label': confirm_label,
                    'cancel_label': cancel_label,
                    })
        return patch_wrapper(decorator, func)
    return wrapper
