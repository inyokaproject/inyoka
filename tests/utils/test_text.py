# -*- coding: utf-8 -*-
"""
    tests.utils.test_utils
    ~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2007-2020 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from unittest import TestCase

from django.test import override_settings

from inyoka.utils.text import human_number, join_pagename, normalize_pagename, increment_string, get_pagetitle, wiki_slugify


class TestHumanNumber(TestCase):
    def test_negative_value(self):
        self.assertEqual(human_number(-1337), -1337)

    def test_zero(self):
        self.assertEqual(human_number(0), 0)

    @override_settings(LANGUAGE_CODE='de-DE')
    def test_masculine(self):
        self.assertEqual(human_number(1, 'masculine'), u'ein')

    @override_settings(LANGUAGE_CODE='de-DE')
    def test_feminine(self):
        self.assertEqual(human_number(1, 'feminine'), u'eine')

    @override_settings(LANGUAGE_CODE='de-DE')
    def test_neuter(self):
        self.assertEqual(human_number(1, 'neuter'), u'ein')

    @override_settings(LANGUAGE_CODE='de-DE')
    def test_german_without_gender(self):
        self.assertEqual(human_number(1), u'eins')

    def test_without_gender(self):
        self.assertEqual(human_number(1), u'one')

    def test_text_value(self):
        self.assertEqual(human_number(10), u'ten')

    def test_text_eleven(self):
        self.assertEqual(human_number(11), u'eleven')

    def test_last_text(self):
        self.assertEqual(human_number(12), u'twelve')

    def test_regular_number(self):
        self.assertEqual(human_number(13), 13)

    def test_everything(self):
        self.assertEqual(human_number(42), 42)


class TestJoinPageName(TestCase):
    def test_join_pagename_with_strings(self):
        self.assertEqual(join_pagename("Foo", "Bar"), "Foo/Bar")
        self.assertEqual(join_pagename("Foo", "Bar/Baz"), "Bar/Baz")
        self.assertEqual(join_pagename("Foo", "./Bar/Baz"), "Foo/Bar/Baz")
        self.assertEqual(join_pagename("Foo", "./Bar"), "Foo/Bar")
        self.assertEqual(join_pagename("Foo/Bar", "../Blah"), "Foo/Blah")
        self.assertEqual(join_pagename("Foo/Bar", "./Blah"), "Foo/Bar/Blah")
        self.assertEqual(join_pagename("Foo", "../../../Blub"), "Blub")

    def test_join_pagename_with_none(self):
        self.assertEqual(join_pagename(None, "Bar"), "Bar")
        self.assertEqual(join_pagename("Bar", None), "Bar")

    def test_join_pagename_with_objects(self):
        class PageDummy(object):
            name = "Dummy"

        self.assertEqual(join_pagename(PageDummy(), PageDummy()), "Dummy/Dummy")


class TestNormalizePagename(TestCase):
    def test_normalize_pagename(self):
        self.assertEqual(normalize_pagename("Foo Bar"), "Foo_Bar")

    def test_normalize_pagename_with_slashes(self):
        self.assertEqual(normalize_pagename("/Foo_Bar/"), "Foo_Bar")

    def test_normalize_pagename_with_disallowed_chars(self):
        self.assertEqual(normalize_pagename("Foo%Bar?#"), "FooBar")

    def test_normalize_pagename_without_strip(self):
        self.assertEqual(normalize_pagename("/Foo Bar", False), "/Foo_Bar")


class TestGetPageTitle(TestCase):
    def test_get_pagetitle_partial(self):
        self.assertEqual(get_pagetitle("Bar/Foo_Bar",full=False),"Foo Bar")

    def test_get_pagetitle_full(self):
        self.assertEqual(get_pagetitle("Bar/Foo_Bar"),"Bar/Foo Bar")


class TestWikiSlugify(TestCase):
    def test_str(self):
        self.assertEqual(wiki_slugify('Test'), 'test')

    def test_unicode(self):
        self.assertEqual(wiki_slugify(u'test'), 'test')
        self.assertEqual(wiki_slugify(u'test🦄'), 'test')
        self.assertEqual(wiki_slugify(u'test乸'), 'test')
        self.assertEqual(wiki_slugify(u'test'), 'test')

    def test_uppercase(self):
        self.assertEqual(wiki_slugify(u'TEST'), 'test')

    def test_umlauts(self):
        self.assertEqual(wiki_slugify(u'Exämple'), 'example')

    def test_whitespaces(self):
        self.assertEqual(wiki_slugify(u'foo bar'), 'foo_bar')

    def test_accents(self):
        self.assertEqual(wiki_slugify(u'Déjà Dup'), 'deja_dup')

    def test_disallowed(self):
        self.assertEqual(wiki_slugify(u'Ex@mple'), 'exmple')
