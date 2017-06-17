# -*- coding: utf-8 -*-
"""
    inyoka.forum.utils
    ~~~~~~~~~~~~~~~~~

    Contains various helper functions for the forum.

    :copyright: (c) 2007-2017 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _

from inyoka.utils.decorators import patch_wrapper
from inyoka.utils.urls import href


def forum_editable_required():

    def wrapper(func):
        def decorator(request, *args, **kwargs):
            pass
            if settings.FORUM_DISABLE_POSTING:
                messages.error(request, _('Post functionality is currently disabled.'))
                return HttpResponseRedirect(href('forum'))
            return func(request, *args, **kwargs)
        return patch_wrapper(decorator, func)
    return wrapper