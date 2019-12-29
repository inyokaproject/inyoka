# -*- coding: utf-8 -*-
"""
    inyoka.utils.templating
    ~~~~~~~~~~~~~~~~~~~~~~~

    This module contains functions for template-related things.

    :copyright: (c) 2007-2020 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import json
import os
import sys
from importlib import import_module

from django.apps import apps
from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.template.context_processors import csrf
from django.forms.widgets import CheckboxInput
from django.template.base import Context as DjangoContext
from django.template.base import TemplateDoesNotExist
from django.template.loaders.base import Loader
from django.utils import six, translation
from django.utils.encoding import force_unicode
from django.utils.functional import Promise
from django.utils.timesince import timesince
from django_mobile import get_flavour
from jinja2 import (
    Environment,
    FileSystemLoader,
    Template,
    TemplateNotFound,
    contextfunction,
)

from inyoka import INYOKA_VERSION
from inyoka.utils.dates import (
    format_date,
    format_datetime,
    format_time,
    format_timetz,
    naturalday)
from inyoka.utils.local import current_request
from inyoka.utils.special_day import check_special_day
from inyoka.utils.text import human_number
from inyoka.utils.urls import href, url_for, urlencode, urlquote

def populate_context_defaults(context, flash=False):
    """Fill in context defaults."""
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
    if global_message and request:
        age_global_message = float(storage['global_message_time'] or 0.0)
        timestamp_user_has_hidden_global_message = user.settings.get(
            'global_message_hidden', 0)
        if timestamp_user_has_hidden_global_message > age_global_message:
            global_message = None

    if request:
        linkmap_model = apps.get_model(app_label='portal', model_name='Linkmap')
        context.update(
            CURRENT_URL=request.build_absolute_uri(),
            USER=user,
            MOBILE=get_flavour() == 'mobile',
            _csrf_token=force_unicode(csrf(request)['csrf_token']),
            special_day_css=check_special_day(),
            linkmap_css=linkmap_model.objects.get_css_basename(),
            LANGUAGE_CODE=settings.LANGUAGE_CODE
        )

        if not flash:
            context['MESSAGES'] = messages.get_messages(request)

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
    )


def load_template(template_name):
    # if available, use dedicated mobile template
    mobile_template_name = template_name
    if get_flavour() == 'mobile':
        path = os.path.splitext(template_name)
        mobile_template_name = '{0}m'.join(path).format(os.extsep)
    try:
        tmpl = jinja_env.get_template(mobile_template_name)
    except TemplateNotFound:
        tmpl = jinja_env.get_template(template_name)
    return tmpl


def render_template(template_name, context, flash=False,
                    populate_defaults=True):
    """Render a template.  You might want to set `req` to `None`."""
    tmpl = load_template(template_name)
    return tmpl.render(context, flash, populate_defaults)


def render_string(source, context):
    tmpl = jinja_env.from_string(source)
    return tmpl.render(context)


def urlencode_filter(value):
    """URL encode a string or dict."""
    if isinstance(value, dict):
        return urlencode(value)
    return urlquote(value)


def ischeckbox_filter(input):
    return isinstance(input, CheckboxInput)


@contextfunction
def csrf_token(context):
    csrf_token = context['_csrf_token']
    if csrf_token == 'NOTPROVIDED':
        return u''
    else:
        return ("<div style='display:none'><input type='hidden' "
                "name='csrfmiddlewaretoken' value='%s' /></div>") % csrf_token


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


class JinjaTemplate(Template):
    def render(self, context, flash=False, populate_defaults=True):
        context = {} if context is None else context
        if isinstance(context, DjangoContext):
            c = context
            context = {}
            for d in c.dicts:
                context.update(d)
            context.pop('csrf_token', None)  # We have our own...
        if populate_defaults:
            populate_context_defaults(context, flash)
        return super(JinjaTemplate, self).render(context)


class InyokaEnvironment(Environment):
    """
    Beefed up version of the jinja environment but without security features
    to improve the performance of the lookups.
    """
    template_class = JinjaTemplate

    def __init__(self):
        template_paths = list(settings.TEMPLATE_DIRS)

        # At compile time, cache the directories to search.
        if not six.PY3:
            fs_encoding = sys.getfilesystemencoding() or sys.getdefaultencoding()
        for app in settings.INSTALLED_APPS:
            try:
                mod = import_module(app)
            except ImportError:
                pass
            template_dir = os.path.join(os.path.dirname(mod.__file__), 'templates')
            if os.path.isdir(template_dir):
                if not six.PY3:
                    template_dir = template_dir.decode(fs_encoding)
                template_paths.append(template_dir)

        loader = FileSystemLoader(template_paths)
        Environment.__init__(self, loader=loader,
                             extensions=['jinja2.ext.i18n', 'jinja2.ext.do'],
                             auto_reload=settings.DEBUG,
                             cache_size=-1)

        self.globals.update(BASE_DOMAIN_NAME=settings.BASE_DOMAIN_NAME,
                            INYOKA_VERSION=INYOKA_VERSION,
                            SETTINGS=settings,
                            REQUEST=current_request,
                            href=href,
                            csrf_token=csrf_token)
        self.filters.update(FILTERS)

        self.install_gettext_translations(translation, newstyle=True)

    def _compile(self, source, filename):
        filename = 'jinja:/' + filename if filename.startswith('/') else filename
        code = compile(source, filename, 'exec')
        return code


class DjangoLoader(Loader):
    is_usable = True

    def load_template(self, template_name, template_dirs=None):
        if template_name.startswith('debug_toolbar'):
            raise TemplateDoesNotExist
        try:
            return load_template(template_name), template_name
        except TemplateNotFound:
            raise TemplateDoesNotExist(template_name)


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

# setup the template environment
jinja_env = InyokaEnvironment()
