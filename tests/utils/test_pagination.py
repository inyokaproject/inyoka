# -*- coding: utf-8 -*-
"""
    tests.utils.test_pagination
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test pagination.

    :copyright: (c) 2012-2021 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import unittest

from django.http import Http404
from django.test import RequestFactory

from inyoka.utils.pagination import Pagination


class TestUtilsPagination(unittest.TestCase):
    def setUp(self):
        self.request = RequestFactory().get('/')
        self.items = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
        self.p = Pagination(self.request, query=self.items, page=1, per_page=3,
                            link='http://localhost/')

    def test_pagination_total_pages(self):
        self.assertEqual(self.p.pages, 5)

    def test_pagination_max_pages(self):
        p = Pagination(self.request, query=self.items, page=1, per_page=2,
                       link='http://localhost/', max_pages=2)
        self.assertEqual(p.pages, 2)

    def test_pagination_one_page(self):
        p = Pagination(self.request, query=self.items, page=1, per_page=5,
                       link='http://localhost/', one_page=True)
        self.assertEqual(p.get_queryset(), self.items)

    def test_pagination_generate_link(self):
        self.assertEqual(self.p.generate_link(1, None), 'http://localhost/')
        self.assertEqual(self.p.generate_link(2, None), 'http://localhost/2/')

    def test_pagination_invalid_page(self):
        with self.assertRaises(Http404):
            Pagination(self.request, query=self.items, page=0, per_page=3)
        with self.assertRaises(Http404):
            Pagination(self.request, query=self.items, page=6, per_page=3)

    def test_pagination_get_queryset(self):
        self.assertEqual(self.p.get_queryset(), [1, 2, 3])
        # needs more tests

    def test_pagination_first(self):
        self.assertEqual(self.p.first, 'http://localhost/')

    def test_pagination_last(self):
        self.assertEqual(self.p.last, 'http://localhost/5/')

    def test_pagination_prev(self):
        self.assertEqual(self.p.prev, False)

    def test_pagination_next(self):
        self.assertEqual(self.p.next, 'http://localhost/2/')

    def test_pagination_list(self):
        expect = [
            {'type': 'current', 'url': 'http://localhost/', 'page': 1},
            {'type': 'link', 'url': 'http://localhost/2/', 'page': 2},
            {'type': 'spacer'},
            {'type': 'link', 'url': 'http://localhost/4/', 'page': 4},
            {'type': 'link', 'url': 'http://localhost/5/', 'page': 5},
        ]
        for l, e in zip(self.p.list(), expect):
            self.assertEqual(l, e)
