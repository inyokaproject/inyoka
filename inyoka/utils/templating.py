"""
    inyoka.utils.templating
    ~~~~~~~~~~~~~~~~~~~~~~~

    This module contains functions for template-related things.

    :copyright: (c) 2007-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import json
from datetime import date
from urllib.parse import quote

from django.apps import apps
from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.forms.widgets import CheckboxInput
from django.template import loader
from django.template.backends.utils import csrf_input
from django.utils import translation
from django.utils.encoding import force_str
from django.utils.functional import Promise
from django.utils.http import urlencode
from django.utils.timesince import timesince

import jinja2
from inyoka import INYOKA_VERSION
from inyoka.utils.dates import (
    format_date,
    format_datetime,
    format_time,
    format_timetz,
    naturalday,
)
from inyoka.utils.local import current_request
from inyoka.utils.special_day import check_special_day
from inyoka.utils.text import human_number
from inyoka.utils.urls import href, url_for


def context_data(request):
    """Fill in context defaults."""
    from inyoka.forum.models import Topic
    from inyoka.ikhaya.models import Event, Report, Suggestion
    from inyoka.portal.models import PrivateMessageEntry
    from inyoka.utils.storage import storage

    user = request.user

    reported = pms = suggestions = events = reported_articles = 0
    if user.is_authenticated:
        can = {'manage_topics': user.has_perm('forum.manage_reported_topic'),
               'article_edit': user.has_perm('ikhaya.change_article'),
               'event_edit': user.has_perm('portal.change_event')}

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
    if global_message:
        age_global_message = float(storage['global_message_time'] or 0.0)
        timestamp_user_has_hidden_global_message = user.settings.get(
            'global_message_hidden', 0)
        if timestamp_user_has_hidden_global_message > age_global_message:
            global_message = None

    linkmap_model = apps.get_model(app_label='portal', model_name='Linkmap')
    context = {
        'CURRENT_URL': request.build_absolute_uri(),
        'current_year': date.today().year,
        'USER': user,
        'special_day_css': check_special_day(),
        'LANGUAGE_CODE': settings.LANGUAGE_CODE,
        'linkmap_css': linkmap_model.objects.get_css_basename(),
        'MESSAGES': messages.get_messages(request),
        'GLOBAL_MESSAGE': global_message,
        'pm_count': pms,
        'report_count': reported,
        'article_report_count': reported_articles,
        'suggestion_count': suggestions,
        'event_count': events,
    }

    # TODO: Replace with django builtins
    context['csrf_token'] = lambda: csrf_input(request)

    if settings.DEBUG:
        from django.db import connection
        context.update(
            sql_queries_count=len(connection.queries),
            sql_queries_time=sum(float(q['time']) for q in connection.queries),
        )

    return context


# TODO: try to get rid of
def render_template(template_name, context, flash=False,
                    populate_defaults=True):
    """Render a template.  You might want to set `req` to `None`."""
    # BIG TODO: This currently return a raw Jinja template instead of a Django Template
    # to support flash/populate_defaults. If we were to take flash from the context instead
    # we could use context_processor and drop this function completly and use Django's render()
    # function.

    tmpl = loader.select_template([template_name])
    try:
        request = current_request._get_current_object()
    except RuntimeError:
        request = None
    return tmpl.render(context, request)


def urlencode_filter(value):
    """URL encode a string or dict."""
    if isinstance(value, dict):
        return urlencode(value)
    return quote(value)


def ischeckbox_filter(input):
    return isinstance(input, CheckboxInput)


class LazyJSONEncoder(json.JSONEncoder):
    """
    Encode a given object as JSON string, taking care of lazy objects. Lazy
    objects, such as ``ugettext_lazy()`` will be forced to unicode.
    """
    def default(self, obj):
        if isinstance(obj, Promise):
            return force_str(obj)
        return super().default(obj)


def json_filter(value):
    """"A wrapper function that uses the :class:`LazyJSONEncoder`"""
    return LazyJSONEncoder().encode(value)


def environment(**options):
    env = jinja2.Environment(**options)

    env.globals.update(BASE_DOMAIN_NAME=settings.BASE_DOMAIN_NAME,
                       INYOKA_VERSION=INYOKA_VERSION,
                       SETTINGS=settings,
                       href=href)
    env.filters.update(FILTERS)

    env.install_gettext_translations(translation, newstyle=True)

    return env


#: Filters that are globally available in the template environment
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
    'timetz': format_timetz,
}
