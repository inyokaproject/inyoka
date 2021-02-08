# -*- coding: utf-8 -*-
"""
    inyoka.utils.pagination
    ~~~~~~~~~~~~~~~~~~~~~~~

    This file helps creating a pagination. It is able to select the right
    database entries and return a subset of the query. The object has methods
    and properties to retrieve the links to other pages, which can be used in
    templates.

    Usage::

        >>> from django.test.client import RequestFactory
        >>> from inyoka.forum.models import Topic
        >>> request = RequestFactory().get('/')
        >>> pagination = Pagination(request,
        ...     Topic.objects.all(), page=5,
        ...     per_page=25, total=500)
        >>> # the database entries on this page
        >>> objects = pagination.get_queryset()

    If the page is out of range, it throws a Http404 exception, when the object
    is created.
    You can pass the optional argument `total` if you already know how
    many entries match your query. If you don't, `Pagination` will use
    a database query to find it out.
    The number of pages can be limited with the optional argument `max_pages`.
    For tables that are quite big it's sometimes useful to use an indexed
    column determinating the position instead of using an offset / limit
    statement. In this case you can use the `rownum_column` argument.
    To get all items on one page, set `one_page=True` or `per_page=0`.

    URL to the first and last page will be accessible through `pagination.first`
    and `pagination.last`.

    Similarly `pagination.prev` and `pagination.next` will return the URL for the
    previous or next page if there is such a page, otherwise return value will
    be False.

    `pagination.list(threshold)` is a generator that yields all URLs to be
    displayed in order as well as necessary "spacers" if pages are omitted. The
    parameter `threshold` determines how many pages are to be displayed
    before/after current page and at beginning and end. Possible yields can take
    three forms:
        - `{ 'type': 'link', 'url': 'http://localhost/', 'page': 1 }`
        - `{ 'type': 'current', 'url': 'http://localhost/2/', 'page': 2 }`
        - `{ 'type': 'spacer' }`

    Caveat: paginations with link functions generated in a closure are
    not pickleable.

    :copyright: (c) 2007-2021 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""


from django.http import Http404
from django.utils.encoding import force_text

from inyoka.utils.urls import urlencode


class Pagination(object):
    """ Handle pagination """

    def __init__(self, request, query, page=1, per_page=10, link=None, total=None,
            rownum_column=None, max_pages=None, one_page=False):
        """ Create pagination object

            :param request: The current request.
            :param query: The objects to paginate. Can be a QuerySet, list or tuple.
            :param page: Current page number.
            :param per_page: Number of items per page.
            :param link: The base url.
            :param total: Total number of items in query, can be None.
            :param rownum_column: Name of the column used to order items.
            :param max_pages: Maximum number of pages.
            :param one_page: If set, show all elements on one page
        """

        self.request = request
        self.query = query
        self.page = int(page)
        self.per_page = int(per_page)
        self.base_link = self._get_base_link(link)
        self.total = self._get_total(total)
        self.rownum_column = rownum_column

        self._queryset = None
        self._first = None
        self._last = None
        self._next = None
        self._prev = None

        if one_page or self.per_page < 1:
            self.per_page = self.total
            self.pages = 1
            self.page = 1
        else:
            self.pages = max(0, (self.total - 1)) // self.per_page + 1

        if max_pages and self.pages > max_pages:
            self.pages = max_pages

        if self.page > self.pages or self.page < 1:
            raise Http404()

        # This unicode/utf-8 conversion exists because of some fancy hacker-bots
        # that try to fuzz the pagination with some extremly invalid unicode data.
        # Catching those here fixes vulerabilty of the whole application.
        enc = lambda v: force_text(v).encode('utf-8') if isinstance(v, str) else v
        self.params = {enc(k): enc(v) for k, v in self.request.GET.items()}

    def _get_base_link(self, link):
        if link is None:
            link = self.request.path
        if isinstance(link, str):
            return link
        else:
            self.generate_link = link

    def _get_total(self, total):
        if total:
            return total
        elif isinstance(self.query, (list, tuple)):
            return len(self.query)
        else:
            return self.query.count()

    def get_queryset(self):
        """ Get objects for current page """

        if self._queryset is not None:
            return self._queryset

        index_first = (self.page - 1) * self.per_page
        index_last = index_first + self.per_page

        if self.rownum_column:
            expr = {'{}__gte'.format(self.rownum_column): index_first,
                    '{}__lt'.format(self.rownum_column): index_last}
            self._queryset = self.query.filter(**expr)
        else:
            self._queryset = self.query[index_first:index_last]

        return self._queryset

    def generate_link(self, page, params):
        """ Get link for page number

        :param page: page number
        :return: A URL string
        """

        if page == 1:
            url = self.base_link
        else:
            url = '{}{}/'.format(self.base_link, page)
        if self.params:
            url = url + '?{}'.format(urlencode(self.params))
        return url

    @property
    def first(self):
        """ Return the url to the first page """
        if self._first is None:
            self._first = self.generate_link(1, self.params)
        return self._first

    @property
    def last(self):
        """ Return the url to the last page """

        if self._last is None:
            self._last = self.generate_link(self.pages, self.params)
        return self._last

    @property
    def prev(self):
        """ Return the url to the previous page, or False if already on first page """

        if self.page <= 1:
            return False
        if self._prev is None:
            self._prev = self.generate_link(self.page - 1, self.params)
        return self._prev

    @property
    def next(self):
        """ Return the url to the last page, or False if already on the last page """

        if self.page >= self.pages:
            return False
        if self._next is None:
            self._next = self.generate_link(self.page + 1, self.params)
        return self._next

    def list(self, threshold=2):
        """ Generator, lists all links for a pagination.

        :param threshold: Number of pages displayed at beginning, end and
                          before/after current page. Other pages are omitted.
        :yields: A small dict containing at least a key `type` which can be 'link',
                 'current' or 'spacer'. All except the 'spacer' will also have
                 keys 'url' and 'page'.
        """

        for num in range(1, self.pages + 1):
            if (num <= threshold or num > (self.pages - threshold) or
                    abs(self.page - num) < threshold):
                was_ellipsis = False
                yield {
                    'type': 'current' if self.page == num else 'link',
                    'page': num,
                    'url': self.generate_link(num, self.params)
                }
            elif not was_ellipsis:
                was_ellipsis = True
                yield {
                    'type': 'spacer'
                }
