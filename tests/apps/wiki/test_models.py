# -*- coding: utf-8 -*-
from django.core.cache import cache

from inyoka.utils.test import TestCase
from inyoka.wiki.models import Page
from inyoka.wiki.utils import CaseSensitiveException


class TestPageManager(TestCase):
    def test_get_by_name_case_sensitive(self):
        """
        Tests that get_by_name does not ignore case.
        """
        Page.objects.create('test', 'test content')

        with self.assertRaises(CaseSensitiveException):
            Page.objects.get_by_name('Test', nocache=True)

    def test_get_by_name_cache_case_sensitive_set(self):
        """
        Tests that get_by_name creates the correkt cache.
        """
        Page.objects.create('Test', 'test content')

        Page.objects.get_by_name('Test')

        self.assertIsNone(cache.get('wiki/page/Test'))
        self.assertIsNotNone(cache.get('wiki/page/test'))
