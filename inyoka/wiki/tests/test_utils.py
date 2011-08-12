# -*- coding: utf-8 -*-
"""
    test_wiki_utils
    ~~~~~~~~~~~~~~~

    Test the wiki utilities.

    :copyright: Copyright 2007 by Armin Ronacher.
    :license: GNU GPL.
"""
from django.test import TestCase
from inyoka.utils.text import join_pagename, normalize_pagename


class TestWikiUtils(TestCase):

    def test_join_pagename(self):
        j = join_pagename
        self.assertEqual(j("Foo", "Bar"), "Foo/Bar")
        self.assertEqual(j("Foo", "Bar/Baz"), "Bar/Baz")
        self.assertEqual(j("Foo", "./Bar/Baz"), "Foo/Bar/Baz")
        self.assertEqual(j("Foo", "./Bar"), "Foo/Bar")
        self.assertEqual(j("Foo/Bar", "../Blah"), "Foo/Blah")
        self.assertEqual(j("Foo/Bar", "./Blah"), "Foo/Bar/Blah")
        self.assertEqual(j("Foo", "../../../Blub"), "Blub")

    def test_normalize_pagename(self):
        n = normalize_pagename
        self.assertEqual(n("Foo Bar"), "Foo_Bar")
        self.assertEqual(n("/Foo_Bar/"), "Foo_Bar")
        self.assertEqual(n("Foo%Bar?#"), "FooBar")
