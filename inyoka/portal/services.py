# -*- coding: utf-8 -*-
"""
    inyoka.portal.services
    ~~~~~~~~~~~~~~~~~~~~~~

    Various services for the portal or all applications.


    :copyright: (c) 2007-2020 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import time
from hashlib import md5
from urlparse import urlparse

from django.conf import settings
from django.contrib.auth.models import Group
from django.db.models.functions import Length
from django.http import Http404
from django.utils.dates import MONTHS, WEEKDAYS

from inyoka.ikhaya.models import Event
from inyoka.portal.user import User
from inyoka.utils.captcha import Captcha
from inyoka.utils.services import SimpleDispatcher
from inyoka.utils.templating import render_template

MIN_AUTOCOMPLETE_CHARS = 3
MAX_AUTOCOMPLETE_ITEMS = 10

dispatcher = SimpleDispatcher()


def autocompletable(string):
    """
    Returns `True` if `string` is autocompletable, e.g. at least
    as long than `MIN_AUTOCOMPLETE_CHARS`.
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
def get_captcha(request):
    captcha = Captcha()
    h = md5(settings.SECRET_KEY)
    h.update(captcha.solution)
    request.session['captcha_solution'] = h.hexdigest()
    response = captcha.get_response()
    # Save the solution for easier testing
    response._captcha_solution = captcha.solution
    return response


@dispatcher.register()
def get_calendar_entry(request):
    if 'url' in request.GET:
        url = request.GET['url']
        slug = urlparse(url)[2][10:]
        if slug.endswith('/'):
            slug = slug[:-1]
    else:
        try:
            slug = request.GET['slug']
        except KeyError:
            raise Http404()
    try:
        event = Event.objects.get(slug=slug)
        if not (event.visible or request.user.has_perm('portal.change_event')):
            raise Http404()
    except Event.DoesNotExist:
        raise Http404()

    data = {
        'event': event,
        'MONTHS': MONTHS,
        'WEEKDAYS': WEEKDAYS,
    }
    return render_template('portal/_calendar_detail.html', data)


@dispatcher.register()
def toggle_sidebar(request):
    if not request.user.is_authenticated:
        return False
    component = request.GET.get('component')
    if component not in ('ikhaya', 'planet', 'admin'):
        component = 'portal'
    component = '_'.join([component, 'sidebar_hidden'])
    if request.GET.get('hide') == 'true':
        request.user.settings[component] = True
    else:
        request.user.settings.pop(component, None)
    request.user.save(update_fields=['settings'])
    return True


@dispatcher.register()
def hide_global_message(request):
    if request.user.is_authenticated:
        request.user.settings['global_message_hidden'] = time.time()
        request.user.save(update_fields=['settings'])
        return True
    return False
