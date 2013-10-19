# -*- coding: utf-8 -*-
"""
    inyoka.ikhaya.services
    ~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2007-2013 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.ikhaya.models import Suggestion
from inyoka.portal.models import User
from inyoka.utils.services import permit_methods, SimpleDispatcher


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
    change_suggestion_assignment=on_change_suggestion_assignment
)
