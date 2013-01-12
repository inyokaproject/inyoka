# -*- coding: utf-8 -*-
"""
    inyoka.portal.services
    ~~~~~~~~~~~~~~~~~~~~~~

    Various services for the portal or all applications.


    :copyright: (c) 2007-2013 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import time
from hashlib import md5
from urlparse import urlparse

from django.conf import settings
from django.http import Http404
from django.utils.dates import MONTHS, WEEKDAYS
from inyoka.portal.user import User, Group
from inyoka.ikhaya.models import Event
from inyoka.utils.text import get_random_password
from inyoka.utils.services import SimpleDispatcher
from inyoka.utils.captcha import Captcha
from inyoka.utils.templating import render_template


def on_get_current_user(request):
    """Get the current user."""
    user = request.user
    return {
        'is_anonymous':     user.is_anonymous,
        'username':         user.username or None,
        'email':            getattr(user, 'email', None),
    }


def on_get_user_list(request):
    q = request.GET.get('q', '')
    if len(q) < 3:
        return
    qs = list(User.objects.filter(username__istartswith=q,
                                  status__exact=1)[:11])
    usernames = [x.username for x in qs]
    if len(qs) > 10:
        usernames[10] = '...'
    return usernames


def on_get_group_list(request):
    q = request.GET.get('q', '')
    #if len(q) < 3:
    #    return
    qs = list(Group.objects.filter(name__istartswith=q,
                                  is_public__exact=True)[:11])
    groupnames = [x.name for x in qs]
    if len(qs) > 10:
        groupnames[10] = '...'
    return groupnames


def on_get_random_password(request):
    return {'password': get_random_password()}


def on_get_captcha(request):
    captcha = Captcha()
    h = md5(settings.SECRET_KEY)
    h.update(captcha.solution)
    request.session['captcha_solution'] = h.digest()
    return captcha.get_response()


def on_get_calendar_entry(request):
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
    except Event.DoesNotExist:
        raise Http404()

    data = {
        'event': event,
        'MONTHS': MONTHS,
        'WEEKDAYS': WEEKDAYS,
    }
    return render_template('portal/_calendar_detail.html', data)


def on_toggle_sidebar(request):
    if not request.user.is_authenticated():
        return False
    component = request.GET.get('component')
    if component not in ('ikhaya', 'planet', 'admin'):
        component = 'portal'
    component = '_'.join([component, 'sidebar_hidden'])
    if request.GET.get('hide') == 'true':
        request.user.settings[component] = True
    else:
        request.user.settings.pop(component)
    request.user.save(update_fields=['settings'])
    return True


def hide_global_message(request):
    if request.user.is_authenticated():
        request.user.settings['global_message_hidden'] = time.time()
        request.user.save(update_fields=['settings'])
        return True
    return False


dispatcher = SimpleDispatcher(
    get_current_user=on_get_current_user,
    get_user_autocompletion=on_get_user_list,
    get_group_autocompletion=on_get_group_list,
    get_random_password=on_get_random_password,
    get_captcha=on_get_captcha,
    get_calendar_entry=on_get_calendar_entry,
    toggle_sidebar=on_toggle_sidebar,
    hide_global_message=hide_global_message
)
