# -*- coding: utf-8 -*-
"""
    inyoka.ikhaya.services
    ~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2007-2015 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.views.decorators.http import require_POST
from inyoka.ikhaya.models import Suggestion
from inyoka.portal.models import User
from inyoka.utils.services import SimpleDispatcher


@require_POST()
def on_change_suggestion_assignment(request):
    post = request.POST
    username, suggestion = post['username'], post['suggestion']
    suggestion = Suggestion.objects.get(id=suggestion)

    if username == '-':
        suggestion.owner = None
        suggestion.save()
    else:
        suggestion.owner = User.objects.get(username__iexact=username)
        suggestion.save()
    return True


dispatcher = SimpleDispatcher(
    change_suggestion_assignment=on_change_suggestion_assignment
)
