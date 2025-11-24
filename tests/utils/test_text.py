"""
    tests.utils.test_utils
    ~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2007-2025 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from unittest import TestCase

from django.test import override_settings

from inyoka.utils.text import (
    get_pagetitle,
    human_number,
    join_pagename,
    normalize_pagename,
    wiki_slugify,
)


class TestHumanNumber(TestCase):
    def test_negative_value(self):
        self.assertEqual(human_number(-1337), -1337)

    def test_zero(self):
        self.assertEqual(human_number(0), 0)

    @override_settings(LANGUAGE_CODE='de-DE')
    def test_masculine(self):
        self.assertEqual(human_number(1, 'masculine'), 'ein')

    @override_settings(LANGUAGE_CODE='de-DE')
    def test_feminine(self):
        self.assertEqual(human_number(1, 'feminine'), 'eine')

    @override_settings(LANGUAGE_CODE='de-DE')
    def test_neuter(self):
        self.assertEqual(human_number(1, 'neuter'), 'ein')

    @override_settings(LANGUAGE_CODE='de-DE')
    def test_german_without_gender(self):
        self.assertEqual(human_number(1), 'eins')

    def test_without_gender(self):
        self.assertEqual(human_number(1), 'one')

    def test_text_value(self):
        self.assertEqual(human_number(10), 'ten')

    def test_text_eleven(self):
        self.assertEqual(human_number(11), 'eleven')

    def test_last_text(self):
        self.assertEqual(human_number(12), 'twelve')

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
        class PageDummy:
            name = "Dummy"

        self.assertEqual(join_pagename(PageDummy(), PageDummy()), "Dummy/Dummy")


class TestNormalizePagename(TestCase):
    def test_normalize_pagename(self):
        self.assertEqual(normalize_pagename("Foo Bar"), "Foo_Bar")

    def test_normalize_pagename_with_slashes(self):
        self.assertEqual(normalize_pagename("/Foo_Bar/"), "Foo_Bar")

    def test_normalize_pagename_with_disallowed_chars(self):
        self.assertEqual(normalize_pagename("Foo%Bar?#"), "FooBar")

    def test_normalize_pagename_unicode(self):
        self.assertEqual(normalize_pagename("FooßBar"), "FooßBar")
        self.assertEqual(normalize_pagename("FooäöüBar"), "FooäöüBar")
        self.assertEqual(normalize_pagename("Foo→Bar"), "Foo→Bar")
        self.assertEqual(normalize_pagename("Foo乸Bar"), "Foo乸Bar")

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
        self.assertEqual(wiki_slugify('test'), 'test')
        self.assertEqual(wiki_slugify('test🦄'), 'test')
        self.assertEqual(wiki_slugify('test乸'), 'test')
        self.assertEqual(wiki_slugify('test'), 'test')

    def test_uppercase(self):
        self.assertEqual(wiki_slugify('TEST'), 'test')

    def test_umlauts(self):
        self.assertEqual(wiki_slugify('Exämple'), 'example')

    def test_whitespaces(self):
        self.assertEqual(wiki_slugify('foo bar'), 'foo_bar')

    def test_accents(self):
        self.assertEqual(wiki_slugify('Déjà Dup'), 'deja_dup')

    def test_disallowed(self):
        self.assertEqual(wiki_slugify('Ex@mple'), 'exmple')
