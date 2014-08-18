#-*- coding: utf-8 -*-
"""
    tests.utils.test_pagination
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test pagination.

    :copyright: (c) 2012-2014 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import unittest
from django.conf import settings
from django.http import Http404
from django.test import TestCase, RequestFactory

from inyoka.utils.pagination import Pagination

class TestUtilsPagination(unittest.TestCase):
	def setUp(self):
		self.request = RequestFactory().get('/')
		self.items = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
		self.p = Pagination(self.request, query=self.items, page=1, per_page=3,
					   link='http://localhost/')

	def test_pagination_total_pages(self):
		self.assertEqual(self.p.pages, 5)

	def test_pagination_first_page(self):
		self.assertEqual(self.p.get_queryset(), [1, 2, 3])

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
			p = Pagination(self.request, query=self.items, page=0, per_page=3)
		with self.assertRaises(Http404):
			p = Pagination(self.request, query=self.items, page=6, per_page=3)

	def test_pagination_generate(self):
		p = Pagination(self.request, query=self.items, page=5, per_page=2,
					   link='http://localhost/')
		expected = {
			'current_page': 5,
			'pages': 8,
			'first': 'http://localhost/',
			'last': 'http://localhost/8/',
			'prev': 'http://localhost/4/',
			'next': 'http://localhost/6/',
			'list': [
				{'type': 'page', 'url': 'http://localhost/',   'current': False, 'name': 1},
				{'type': 'page', 'url': 'http://localhost/2/', 'current': False, 'name': 2},
				{'type': 'spacer'},
				{'type': 'page', 'url': 'http://localhost/4/', 'current': False, 'name': 4},
				{'type': 'page', 'url': 'http://localhost/5/', 'current': True,  'name': 5},
				{'type': 'page', 'url': 'http://localhost/6/', 'current': False, 'name': 6},
				{'type': 'page', 'url': 'http://localhost/7/', 'current': False, 'name': 7},
				{'type': 'page', 'url': 'http://localhost/8/', 'current': False, 'name': 8},
			]
		}
		self.assertEqual(p.generate(threshold=2), expected)
