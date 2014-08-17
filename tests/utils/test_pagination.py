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

	def test_pagination_total_pages(self):
		p = Pagination(self.request, query=self.items, page=1, per_page=5, 
					   link='http://localhost/')
		self.assertEqual(p.pages, 3)

	def test_pagination_first_page(self):
		p = Pagination(self.request, query=self.items, page=1, per_page=5, 
					   link='http://localhost/')
		self.assertEqual(p.get_queryset(), [1, 2, 3, 4, 5])

	def test_pagination_one_page(self):
		p = Pagination(self.request, query=self.items, page=1, per_page=5, 
					   link='http://localhost/', one_page=True)
		self.assertEqual(p.get_queryset(), self.items)

	def test_pagination_generate_link(self):
		p = Pagination(self.request, query=self.items, page=1, per_page=5, 
					   link='http://localhost/')
		self.assertEqual(p.generate_link(1, None), 'http://localhost/')
		self.assertEqual(p.generate_link(2, None), 'http://localhost/2/')

	def test_pagination_invalid_page(self):
		with self.assertRaises(Http404):
			p = Pagination(self.request, query=self.items, page=0, per_page=5)
		with self.assertRaises(Http404):
			p = Pagination(self.request, query=self.items, page=4, per_page=5)

