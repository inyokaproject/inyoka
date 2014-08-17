# -*- coding: utf-8 -*-
"""
    inyoka.utils.pagination
    ~~~~~~~~~~~~~~~~~~~~~~~

    This file helps creating a pagination. It is able to select the right 
    database entries and convert them into a dict that can be used in templates

    Usage::

        >>> from django.test.client import RequestFactory
        >>> from inyoka.forum.models import Topic
        >>> request = RequestFactory().get('/')
        >>> pagination = Pagination(request,
        ...     Topic.objects.all(), page=5,
        ...     per_page=25, total=500)
        >>> # the database entries on this page
        >>> objects = pagination.get_queryset()
        >>> # the generated dict for the pagination
        >>> pagination_dict = pagination.generate()

    The dict will have the following structure:
        {
        'current_page': 6,
        'pages': 10,
        'first': 'http://localhost/',
        'last': 'http://localhost/10',
        'prev': 'http://localhost/5',
        'next': 'http://localhost/7',
        'list': [
                {'type': 'page', 'url': 'http://localhost/',    'current': False, 'name': 1},
                {'type': 'page', 'url': 'http://localhost/2/',  'current': False, 'name': 1},
                {'type': 'spacer'},
                {'type': 'page', 'url': 'http://localhost/5/',  'current': False, 'name': 5},
                {'type': 'page', 'url': 'http://localhost/6/',  'current': True,  'name': 6},
                {'type': 'page', 'url': 'http://localhost/7/',  'current': False, 'name': 7},
                {'type': 'spacer'},
                {'type': 'page', 'url': 'http://localhost/9/',  'current': False, 'name': 9},
                {'type': 'page', 'url': 'http://localhost/10/', 'current': False, 'name': 10},
                ],
        }

    If the page is out of range, it throws a Http404 exception.
    You can pass the optional argument `total` if you already know how
    many entries match your query. If you don't, `Pagination` will use
    a database query to find it out.
    The number of pages can be limited with the optional argument `max_pages`.
    For tables that are quite big it's sometimes useful to use an indexed
    column determinating the position instead of using an offset / limit
    statement. In this case you can use the `rownum_column` argument.

    Caveat: paginations with link functions generated in a closure are
    not pickleable.

    :copyright: (c) 2007-2014 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import division

import math

from django.http import Http404
from django.utils.encoding import force_unicode

from inyoka.utils.urls import urlencode


class Pagination(object):
    """ Handle pagination """

    def __init__(self, request, query, page, per_page=10, link=None, total=None,
                       rownum_column=None, max_pages=None, one_page=False):
        """ Create pagination object

            :param request: The current request.
            :param query: The paginated objects, can be a list or tuple
            :param page: Current page number.
            :param per_page: Number of items per page.
            :param link: The base url.
            :param total: Total number of items in query, can be None.
            :param rownum_column: Name of the column used to order items.
            :param max_pages: Maximum number of pages.
            :param one_page: If set, show all elements on one page
        """

        self.request       = request
        self.query         = query
        self.page          = int(page)
        self.per_page      = int(per_page)
        self.base_link     = self._get_base_link(link)
        self.total         = self._get_total(total)
        self.rownum_column = rownum_column
        self.pages         = max(0, (self.total-1)) // self.per_page + 1
        self.queryset      = None

        if one_page:
            self.per_page = self.total
            self.pages = 1

        if max_pages and self.pages > max_pages:
            self.pages = max_pages

        if self.page > self.pages or self.page < 1:
            raise Http404()

        # TODO: is this necessary? Do we ever pass GET-parameters in pagination links?
        # This unicode/utf-8 conversion exists because of some fancy hacker-bots
        # that try to fuzz the pagination with some extremly invalid unicode data.
        # Catching those here fixes vulerabilty of the whole application.
        enc = lambda v: force_unicode(v).encode('utf-8') if isinstance(v, basestring) else v
        self.params = {enc(k): enc(v) for k, v in self.request.GET.iteritems()}

    def _get_base_link(self, link):
        if link is None:
            link = self.request.path
        if isinstance(link, basestring):
            return link
        else:
            self.generate_link = link

    def _get_total(self, total):
        if total:
            return total
        elif isinstance(self.query, (list,tuple)):
            return len(self.query)
        else:
            return self.query.count()

    def get_queryset(self):
        """ Get objects for current page """

        if self.queryset is not None:
            return self.queryset

        index_first = (self.page - 1) * self.per_page
        index_last = index_first + self.per_page

        if self.rownum_column:
            expr = {'{}__gte'.format(self.rownum_column): index_first,
                    '{}__lt'.format(self.rownum_column): index_last}
            self.queryset = self.query.filter(**expr)
        else:
            self.queryset = self.query[index_first:index_last]

        return self.queryset

    def generate_link(self, page, params):
        """ Get link for page number

        :param page: page number
        :return: A URL string
        """

        if page == 1:
            url = self.base_link
        elif self.params:
            url = u'{}{}?{}/'.format(self.base_link, page, urlencode(self.params))
        else:
            url = u'{}{}/'.format(self.base_link, page)
        return url

    def generate(self, threshold=2):
        """ Generate a pagination dict with links and information to be used in 
            templates

        :param threshold: Number of pages displayed at beginning, end and 
                          before/after current page. Other pages are omitted.
        :return: Dict with all links and information
        """

        result_dict = {'pages':         self.pages,
                       'current_page':  self.page,
                       'list':          [],
                      }

        if self.page > 2:
            result_dict['first'] = self.generate_link(1, self.params)

        if self.page < (self.pages-1):
            result_dict['last'] = self.generate_link(self.pages, self.params)

        if self.page < self.pages:
            result_dict['next'] = self.generate_link(self.page + 1, self.params)

        if self.page > 1:
            result_dict['prev'] = self.generate_link(self.page - 1, self.params)

        for num in xrange(1, self.pages+1):
            if num <= threshold or num > (self.pages-threshold) or \
               abs(self.page - num) < threshold:
                was_ellipsis = False
                result_dict['list'] += [{'type': 'page',
                                         'url': self.generate_link(num, self.params),
                                         'current': (num == self.page),
                                         'name': num, }]
            elif not was_ellipsis:
                result_dict['list'] += [{'type': 'spacer'}]
                was_ellipsis = True

        return result_dict
