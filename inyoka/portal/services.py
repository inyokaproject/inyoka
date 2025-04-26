"""
    inyoka.portal.services
    ~~~~~~~~~~~~~~~~~~~~~~

    Various services for the portal or all applications.


    :copyright: (c) 2007-2025 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import time

from django.contrib.auth.models import Group
from django.db.models.functions import Length

from inyoka.portal.user import User
from inyoka.utils.services import SimpleDispatcher

MIN_AUTOCOMPLETE_CHARS = 3
MAX_AUTOCOMPLETE_ITEMS = 10

dispatcher = SimpleDispatcher()


def autocompletable(string):
    """
    Returns `True` if `string` is autocompletable, e.g. at least
    as long as `MIN_AUTOCOMPLETE_CHARS`.
    """
    return len(string) >= MIN_AUTOCOMPLETE_CHARS


@dispatcher.register()
def get_user_autocompletion(request):
    q = request.GET.get('q', '')
    if not autocompletable(q):
        return
    usernames = User.objects.filter(username__istartswith=q, status__exact=1)\
                            .order_by(Length('username').asc())\
                            .values_list('username', flat=True)[:MAX_AUTOCOMPLETE_ITEMS]
    return list(usernames)


@dispatcher.register()
def get_group_autocompletion(request):
    q = request.GET.get('q', '')
    if not autocompletable(q):
        return
    groupnames = Group.objects.filter(name__istartswith=q)\
                              .order_by(Length('name').asc())\
                              .values_list('name', flat=True)[:MAX_AUTOCOMPLETE_ITEMS]
    return list(groupnames)


@dispatcher.register()
def hide_global_message(request):
    if request.user.is_authenticated:
        request.user.settings['global_message_hidden'] = time.time()
        request.user.save(update_fields=['settings'])
        return True
    return False
