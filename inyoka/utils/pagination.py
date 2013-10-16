# -*- coding: utf-8 -*-
"""
    inyoka.utils.pagination
    ~~~~~~~~~~~~~~~~~~~~~~~

    This file helps creating a pagination. It's able to generate the HTML
    source and to select the right database entries.

    Usage::

        >>> from django.test.client import RequestFactory
        >>> from inyoka.forum.models import Topic
        >>> request = RequestFactory().get('/')
        >>> pagination = Pagination(request,
        ...     Topic.objects.all(), page=5,
        ...     per_page=25, total=500)
        >>> # the database entries on this page
        >>> objects = pagination.get_queryset()
        >>> # the generated HTML code for the pagination
        >>> html = pagination.generate()

    If the page is out of range, it throws a Http404 exception.
    You can pass the optional argument `total` if you already know how
    many entries match your query. If you don't, `Pagination` will use
    a database query to find it out.
    For tables that are quite big it's sometimes useful to use an indexed
    column determinating the position instead of using an offset / limit
    statement. In this case you can use the `rownum_column` argument.

    Caveat: paginations with link functions generated in a closure are
    not pickleable.

    :copyright: (c) 2007-2013 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from __future__ import division

import math

from django.http import Http404, HttpResponseRedirect
from django.utils.html import escape
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext as _

from django_mobile import get_flavour
from inyoka.utils.urls import urlencode


class Pagination(object):

    def __init__(self, request, query, page, per_page=10, link=None,
                 total=None, rownum_column=None):
        self.page = int(page)
        self.rownum_column = rownum_column
        self.per_page = per_page
        self.query = query

        if total:
            self.total = total
        elif isinstance(query, (list, tuple)):
            self.total = len(query)
        else:
            self.total = query.count()

        if self.per_page == 0:
            # Display all entries on one page
            self.max_pages = 1
        else:
            self.max_pages = max(0, self.total - 1) // self.per_page + 1

        if self.page > self.max_pages:
            raise Http404()

        if link is None:
            link = request.path
        self.parameters = request.GET
        if isinstance(link, basestring):
            self.link_base = link
        else:
            self.generate_link = link

        self.needs_redirect_to = None
        if self.total and self.total / per_page < 1 and page > 1:
            url = self.generate_link(1, dict(request.GET.lists()))
            self.needs_redirect_to = lambda: HttpResponseRedirect(url)

    @property
    def is_last_page(self):
        return self.page == self.max_pages

    @property
    def has_objects(self):
        return bool(max(0, self.total - 1) // self.per_page + 1)

    def get_queryset(self):
        idx = (self.page - 1) * self.per_page
        if self.rownum_column:
            expr = {'%s__gte' % self.rownum_column: idx,
                    '%s__lt' % self.rownum_column: idx + self.per_page}
            result = self.query.filter(**expr)
        else:
            result = self.query[idx:idx + self.per_page]
        return result

    def generate_link(self, page, params):
        if page == 1:
            url = self.link_base
        else:
            url = u'%s%d/' % (self.link_base, page)
        return url + (params and u'?' + urlencode(params) or u'')

    def generate(self, position=None, threshold=2, show_next_link=True,
                 show_prev_link=True):
        if get_flavour() == 'mobile':
            return self.generate_mobile()
        normal = u'<a href="%(href)s" class="pageselect">%(page)d</a>'
        active = u'<span class="pageselect active">%(page)d</span>'
        ellipsis = u'<span class="ellipsis"> … </span>'
        was_ellipsis = False
        result = []
        add = result.append
        pages = 1
        if self.total:
            pages = max(0, self.total - 1) // self.per_page + 1

        # This unicode/utf-8 conversion exists because of some fancy hacker-bots
        # that try to fuzz the pagination with some extremly invalid unicode data.
        # Catching those here fixes vulerabilty of the whole application.
        enc = lambda v: force_unicode(v).encode('utf-8') if isinstance(v, basestring) else v
        params = {enc(k): enc(v) for k, v in self.parameters.iteritems()}

        half_threshold = max(math.ceil(threshold / 2.0), 2)
        for num in xrange(1, pages + 1):
            if num <= threshold or num > pages - threshold or\
               abs(self.page - num) < half_threshold:
                if result and result[-1] != ellipsis:
                    add(u'<span class="comma">, </span>')
                was_ellipsis = False
                link = self.generate_link(num, params)
                if num == self.page:
                    template = active
                else:
                    template = normal
                add(template % {
                    'href': escape(link),
                    'page': num,
                })
            elif not was_ellipsis:
                was_ellipsis = True
                add(ellipsis)

        if show_next_link:
            if self.page < pages:
                link = self.generate_link(self.page + 1, params)
                tmpl = u''.join([u'<a href="%s" class="next">',
                                    _(u'Next »'), u'</a>'])
                add(tmpl % escape(link))
            else:
                add(u''.join([u'<span class="disabled next">',
                                    _(u'Next »'), u'</span>']))

        if show_prev_link:
            if self.page > 1:
                link = self.generate_link(self.page - 1, params)
                tmpl = u''.join([u'<a href="%s" class="prev">',
                                    _(u'« Previous'), u'</a>'])
                result.insert(0, tmpl % escape(link))
            else:
                result.insert(0, (u''.join([u'<span class="disabled prev">',
                                    _(u'« Previous'), u'</span>'])))

        class_ = 'pagination'
        if position:
            class_ += ' pagination_' + position
        return u'<div class="%s">%s<div style="clear: both">' \
               u'</div></div>' % (class_, u''.join(result))

    def generate_mobile(self):
        # This unicode/utf-8 conversion exists because of some fancy hacker-bots
        # that try to fuzz the pagination with some extremly invalid unicode data.
        # Catching those here fixes vulerabilty of the whole application.
        _get_v = lambda v: force_unicode(v).encode('utf-8') if isinstance(v, basestring) else v

        pages = 1
        if self.total:
            pages = max(0, self.total - 1) // self.per_page + 1

        params = {force_unicode(k).encode('utf-8'): _get_v(v)
                  for k, v in self.parameters.iteritems()}
        s = u''.join([
            u'<div class="pagination">',
            u'<a href="{first_link}" class="prev first">«</a>' if self.page > 1 else '',
            u'<a href="{prev_link}" class="prev">{prev_label}</a>' if self.page > 1 else '',
            u'<span class="active">{current_label} {page} / {max_pages}</span>',
            u'<a href="{next_link}" class="next">{next_label}</a>' if self.page < pages else '',
            u'<a href="{last_link}" class="next last">»</a>' if self.page < pages else '',
            u'<span style="display: none;" class="link_base">{link_base}</span>',
            u'</div>',
        ])
        return s.format(
            current_label=_(u'Page'),
            first_link=self.generate_link(1, params),
            last_link=self.generate_link(self.max_pages, params),
            link_base=self.generate_link(1, params),
            max_pages=self.max_pages,
            next_label=_(u'Next »'),
            next_link=self.generate_link(min(self.page + 1, self.max_pages), params),
            prev_label=_(u'« Previous'),
            prev_link=self.generate_link(max(self.page - 1, 1), params),
            page=self.page
        )
