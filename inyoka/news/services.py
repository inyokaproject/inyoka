# -*- coding: utf-8 -*-
"""
    inyoka.news.services
    ~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2007-2012 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.utils.services import SimpleDispatcher, permit_methods
from inyoka.news.models import Suggestion
from inyoka.portal.models import User


@permit_methods(('POST',))
def on_change_suggestion_assignment(request):
    post = request.POST
    username, suggestion = post['username'], post['suggestion']
    suggestion = Suggestion.objects.get(id=suggestion)

    if username == '-':
        suggestion.owner = None
        suggestion.save()
    else:
        suggestion.owner = User.objects.get(username)
        suggestion.save()
    return True


dispatcher = SimpleDispatcher(
    change_suggestion_assignment = on_change_suggestion_assignment
)
