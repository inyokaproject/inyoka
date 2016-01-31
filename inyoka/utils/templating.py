# -*- coding: utf-8 -*-
"""
    inyoka.utils.templating
    ~~~~~~~~~~~~~~~~~~~~~~~

    This module contains functions for template-related things.

    :copyright: (c) 2007-2016 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import json
import os

import jinja2
from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.forms.widgets import CheckboxInput
from django.template.backends import jinja2 as jinja2backend
from django.template.loader import get_template
from django.utils import translation
from django.utils.encoding import force_unicode
from django.utils.functional import Promise
from django.utils.timesince import timesince
from django_mobile import get_flavour
from inyoka import INYOKA_VERSION
from inyoka.utils.dates import (
    format_date,
    format_datetime,
    format_time,
    naturalday,
)
from inyoka.utils.local import current_request
from inyoka.utils.special_day import check_special_day
from inyoka.utils.text import human_number
from inyoka.utils.urls import href, url_for, urlencode, urlquote


def inyoka_environment(**options):
    env = jinja2.Environment(**options)
    env.install_gettext_translations(translation, newstyle=True)
    env.filters.update(FILTERS)
    env.globals.update(
        INYOKA_VERSION=INYOKA_VERSION,
        SETTINGS=settings,
        href=href,
    )
    return env


def render_template(template_name, context, request=None, flash=False, populate_defaults=True):
    """Render a template.  You might want to set `req` to `None`."""
    template = get_template(template_name)
    if populate_defaults:
        populate_context_defaults(context)
    if flash:
        context['MESSAGES'] = messages.get_messages(request)
    return template.render(context=context, request=request)


# TODO: clean this mess up.
def populate_context_defaults(context, flash=False):
    """Fill in context defaults."""
    from inyoka.forum.acl import have_privilege
    from inyoka.forum.models import Topic
    from inyoka.portal.models import PrivateMessageEntry
    from inyoka.utils.storage import storage
    from inyoka.ikhaya.models import Suggestion, Event, Report

    try:
        request = current_request._get_current_object()
        user = request.user
    except (RuntimeError, AttributeError):
        request = None
        user = None

    reported = pms = suggestions = events = reported_articles = 0
    if request and user.is_authenticated():
        can = {'manage_topics': user.can('manage_topics'),
               'article_edit': user.can('article_edit'),
               'event_edit': user.can('event_edit')}

        keys = ['portal/pm_count/%s' % user.id]

        if can['manage_topics']:
            keys.append('forum/reported_topic_count')
        if can['article_edit']:
            keys.append('ikhaya/suggestion_count')
            keys.append('ikhaya/reported_article_count')
        if can['event_edit']:
            keys.append('ikhaya/event_count')

        cached_values = cache.get_many(keys)
        to_update = {}

        key = 'portal/pm_count/%s' % user.id
        pms = cached_values.get(key)
        if pms is None:
            pms = PrivateMessageEntry.objects \
                .filter(user__id=user.id, read=False) \
                .exclude(folder=None).count()
            to_update[key] = pms
        if can['manage_topics']:
            key = 'forum/reported_topic_count'
            reported = cached_values.get(key)
            if reported is None:
                reported = Topic.objects.filter(reporter__id__isnull=False) \
                                        .count()
                to_update[key] = reported
        if can['article_edit']:
            key = 'ikhaya/suggestion_count'
            suggestions = cached_values.get(key)
            if suggestions is None:
                suggestions = Suggestion.objects.all().count()
                to_update[key] = suggestions
            key = 'ikhaya/reported_article_count'
            reported_articles = cached_values.get(key)
            if reported_articles is None:
                reported_articles = Report.objects\
                    .filter(solved=False, deleted=False).count()
                to_update[key] = reported_articles
        if can['event_edit']:
            key = 'ikhaya/event_count'
            events = cached_values.get(key)
            if events is None:
                events = Event.objects.filter(visible=False).all().count()
                to_update[key] = events

        if to_update:
            cache.set_many(to_update)

    # we don't need to use cache here because storage does this for us
    global_message = storage['global_message_rendered']
    if global_message and request:
        if user.settings.get('global_message_hidden', 0) > \
                float(storage['global_message_time'] or 0.0):
            global_message = None

    if request:
        context.update(
            XHTML_DTD=get_dtd(),
            CURRENT_URL=request.build_absolute_uri(),
            USER=user,
            BREADCRUMB=Breadcrumb(),
            MOBILE=get_flavour() == 'mobile',
            special_day_css=check_special_day(),
            REQUEST=request,
        )

    if settings.DEBUG:
        from django.db import connection
        context.update(
            sql_queries_count=len(connection.queries),
            sql_queries_time=sum(float(q['time']) for q in connection.queries),
        )

    context.update(
        GLOBAL_MESSAGE=global_message,
        pm_count=pms,
        report_count=reported,
        article_report_count=reported_articles,
        suggestion_count=suggestions,
        event_count=events,
        have_privilege=have_privilege,
    )


inyoka_dtd = None


# TODO: Evaluate if we still need this.
def get_dtd():
    """
    This returns either our dtd + xml comment.
    """
    global inyoka_dtd
    if inyoka_dtd is None:
        if settings.DEBUG:
            path = os.path.realpath(os.path.join(os.path.dirname(__file__),
                                                 'static',
                                                 'xhtml1-strict-uu.dtd'))
        else:
            path = href('static', 'xhtml1-strict-uu.dtd')
        inyoka_dtd = u'<!DOCTYPE html SYSTEM "%s">' % path

    return u'<?xml version="1.0" encoding="utf-8"?>\n' + inyoka_dtd


# TODO: Find a better way to do this.
class Breadcrumb(object):
    """
    Class to dynamically generate breadcrumb and title trace.
    """

    def __init__(self):
        self.path = []
        self.final = False

    def append(self, value, link=None, title=False, position=None):
        value = jinja2.escape(value)
        if position is None:
            self.path.append((value, link, title))
        else:
            self.path.insert(position, (value, link, title))

    def render(self, target='breadcrumb'):
        if not self.final:
            base_name = settings.BASE_DOMAIN_NAME.rsplit(':', 1)[0]
            self.path.append((base_name, href('portal'), True))
            self.path.reverse()
            self.final = True
        if target == 'breadcrumb':
            result = []
            for element in self.path:
                result.append(u'<a href="{0}">{1}</a>'.format(element[1],
                                                              element[0]))
            return u' › '.join(result)
        elif target == 'appheader':
            if len(self.path) < 2:
                context = {'fallback': True}
            else:
                context = {
                    'h1_text': self.path[1][0],
                    'h1_link': self.path[1][1],
                    'h2_text': self.path[-1][0],
                    'h2_link': self.path[-1][1],
                }
            return render_template('appheader.html', context, populate_defaults=False)
        elif target == 'title':
            return u' › '.join(i[0] for i in self.path[::-1] if i[2])


# TODO: for the rest of this file: evaluate if we need these things.
def urlencode_filter(value):
    """URL encode a string or dict."""
    if isinstance(value, dict):
        return urlencode(value)
    return urlquote(value)


def ischeckbox_filter(input):
    return isinstance(input, CheckboxInput)


class LazyJSONEncoder(json.JSONEncoder):
    """
    Encode a given object as JSON string, taking care of lazy objects. Lazy
    objects, such as ``ugettext_lazy()`` will be forced to unicode.
    """
    def default(self, obj):
        if isinstance(obj, Promise):
            return force_unicode(obj)
        return super(LazyJSONEncoder, self).default(obj)


def json_filter(value):
    """"A wrapper function that uses the :class:`LazyJSONEncoder`"""
    return LazyJSONEncoder().encode(value)


FILTERS = {
    'timedeltaformat': timesince,
    'hnumber': human_number,
    'url': url_for,
    'urlencode': urlencode_filter,
    'jsonencode': json_filter,
    'ischeckbox': ischeckbox_filter,
    # L10N aware variants of Django's filters. They all are patched to use
    # DATE_FORMAT (naturalday and format_date), DATETIME_FORMAT (format_datetime),
    # and TIME_FORMAT (format_time) from the formats module and not the relevant
    # variables from settings.py
    'naturalday': naturalday,
    'date': format_date,
    'datetime': format_datetime,
    'time': format_time,
}
