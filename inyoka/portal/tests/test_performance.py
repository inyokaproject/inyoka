#-*- coding: utf-8 -*-
"""
    inyoka.portal.tests.test_performance
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from timeit import Timer

from django.test import TestCase
from django.test.client import Client


class TestResponseTime(TestCase):

    def setUp(self):
        self.client = Client()

    def test_time(self):
        def run_request():
            self.client.get('/')
        timer = Timer(run_request)
        #print timer.timeit(2000)
        #self.assert_(False)
