# -*- coding: utf-8 -*-
from django.core.cache import cache

from inyoka.utils.test import TestCase
from inyoka.wiki.models import Page


class TestPageManager(TestCase):
    def test_get_by_name_case_sensitive(self):
        """
        Tests that get_by_name ignores case.
        """
        Page.objects.create('test', 'test content')

        p1 = Page.objects.get_by_name('test', nocache=True)
        p2 = Page.objects.get_by_name('Test', nocache=True)

        self.assertEqual(p1, p2)

    def test_get_by_name_cache_case_sensitive_set(self):
        """
        Tests that get_by_name creates the correkt cache.
        """
        p = Page.objects.create('test', 'test content')

        Page.objects.get_by_name('Test')

        self.assertIsNone(cache.get('wiki/page/Test'))
        self.assertIsNotNone(cache.get('wiki/page/test'))

    def test_get_by_name_cache_case_sensitive_get(self):
        """
        Tests that get_by_name get element with different case from the cache.
        """
        p = Page.objects.create('test', 'test content')
        Page.objects.get_by_name('test')  # Fill the cache

        with self.assertNumQueries(0):
            Page.objects.get_by_name('Test')
