# -*- coding: utf-8 -*-
"""
    inyoka.utils.templating
    ~~~~~~~~~~~~~~~~~~~~~~~

    This module contains functions for template-related things.

    :copyright: (c) 2007-2014 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import os
import json
from glob import glob

from django.conf import settings
from django.contrib import messages
from django.core.context_processors import csrf
from django.template.base import Context as DjangoContext
from django.template.base import TemplateDoesNotExist
from django.template.loader import BaseLoader
from django.utils import translation
from django.utils.encoding import force_unicode
from django.utils.functional import Promise
from django.utils.timesince import timesince
from django_mobile import get_flavour
from jinja2 import (escape, Template, Environment, contextfunction,
    TemplateNotFound, FileSystemLoader)

from inyoka import INYOKA_REVISION
from inyoka.utils.cache import request_cache
from inyoka.utils.dates import format_date, format_datetime, format_time, naturalday
from inyoka.utils.local import current_request
from inyoka.utils.text import human_number
from inyoka.utils.urls import href, url_for, urlquote, urlencode


# path to the dtd.  In debug mode we refer to the file system, otherwise
# URL.  We do that because the firefox validator extension is unable to
# load DTDs from URLs...  On first rendering the path is calculated because
# of circular imports "href()" could cause.
inyoka_dtd = None


def get_dtd():
    """
    This returns either our dtd or our dtd + xml comment.  Neither is stricly
    valid as XML documents with custom doctypes must be served as XML but
    currently as MSIE is pain in the ass we have to workaround that IE bug
    by removing the XML PI comment.
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

    try:
        if 'msie' in current_request.META['HTTP_USER_AGENT'].lower():
            return inyoka_dtd
    except Exception:
        pass
    return u'<?xml version="1.0" encoding="utf-8"?>\n' + inyoka_dtd


class Breadcrumb(object):
    """
    Class to dynamically generate breadcrumb and title trace.
    """

    def __init__(self):
        self.path = []
        self.final = False

    def append(self, value, link=None, title=False, position=None):
        value = escape(value)
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

        cached_values = request_cache.get_many(keys)
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
            request_cache.set_many(to_update)

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
            _csrf_token=force_unicode(csrf(request)['csrf_token'])
        )

        if not flash:
            context['MESSAGES'] = messages.get_messages(request)

    context.update(
        GLOBAL_MESSAGE=global_message,
        OPENID_PROVIDERS=settings.OPENID_PROVIDERS,
        pm_count=pms,
        report_count=reported,
        article_report_count=reported_articles,
        suggestion_count=suggestions,
        event_count=events,
        have_privilege=have_privilege,
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

        template_paths.extend(glob(os.path.join(os.path.dirname(__file__),
                                                os.pardir, '*/templates')))
        loader = FileSystemLoader(template_paths)
        Environment.__init__(self, loader=loader,
                             extensions=['jinja2.ext.i18n', 'jinja2.ext.do'],
                             auto_reload=settings.DEBUG,
                             cache_size=-1)

        self.globals.update(INYOKA_REVISION=INYOKA_REVISION,
                            SETTINGS=settings,
                            REQUEST=current_request,
                            href=href,
                            csrf_token=csrf_token)
        self.filters.update(FILTERS)

        self.install_gettext_translations(translation, newstyle=True)

    def _compile(self, source, filename):
        filename = 'jinja:/' + filename if filename.startswith('/') \
                                        else filename
        code = compile(source, filename, 'exec')
        return code


class DjangoLoader(BaseLoader):
    is_usable = True

    def load_template(self, template_name, template_dirs=None):
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
    # L10N aware variants of Django's filters. They all are patched to use
    # DATE_FORMAT (naturalday and format_date), DATETIME_FORMAT (format_datetime),
    # and TIME_FORMAT (format_time) from the formats module and not the relevant
    # variables from settings.py
    'naturalday': naturalday,
    'date': format_date,
    'datetime': format_datetime,
    'time': format_time,
}

# setup the template environment
jinja_env = InyokaEnvironment()
