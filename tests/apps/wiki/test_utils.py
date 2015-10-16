# -*- coding: utf-8 -*-
"""
    tests.apps.wiki.test_utils
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test the wiki utilities like join_pagename and normalize_pagename.

    :copyright: Copyright 2007 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from inyoka.utils.test import TestCase
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
