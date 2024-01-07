"""
    inyoka.ikhaya.services
    ~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2007-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from inyoka.ikhaya.models import Suggestion
from inyoka.portal.models import User
from inyoka.utils.services import SimpleDispatcher


dispatcher = SimpleDispatcher()


@require_POST
@dispatcher.register()
def change_suggestion_assignment(request):
    post = request.POST

    if 'username' not in post or 'suggestion' not in post:
        return HttpResponseBadRequest()

    username, suggestion = post['username'], post['suggestion']
    suggestion = get_object_or_404(Suggestion, id=suggestion)

    if username == '-':
        suggestion.owner = None
    else:
        suggestion.owner = get_object_or_404(User, username__iexact=username)

    suggestion.save()
    return True
