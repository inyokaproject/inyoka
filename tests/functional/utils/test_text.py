# -*- coding: utf-8 -*-
"""
    tests.functional.utils.test_utils
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: Copyright 2007 by Armin Ronacher.
    :license: GNU GPL.
"""
from django.test import TestCase
from inyoka.utils.text import get_next_increment, human_number


class TestText(TestCase):

    def test_get_next_increment(self):
        self.assertEqual(get_next_increment(['cat', 'cat10', 'cat2'], u'cat'),
                         u'cat-11')
        self.assertEqual(get_next_increment(['cat', 'cat2'], u'cat'),
                         u'cat-3')
        self.assertEqual(get_next_increment(['cat', 'cat1'], u'cat'),
                         u'cat-2')
        self.assertEqual(get_next_increment([], u'cat'),
                         u'cat')
        self.assertEqual(get_next_increment(['cat'], u'cat'),
                         u'cat-2')
        self.assertEqual(get_next_increment(['cat', 'cat10', 'cat2'], u'cat', 3),
                         u'-11')
        self.assertEqual(get_next_increment(['cat', 'cat100'], u'cat', 3),
                         u'-101')

    def test_human_number(self):
        self.assertEqual(human_number(-1337), -1337)
        self.assertEqual(human_number(0), 0)
        self.assertEqual(human_number(1, 'masculine'), u'ein')
        self.assertEqual(human_number(1, 'feminine'), u'eine')
        self.assertEqual(human_number(1, 'neuter'), u'ein')
        self.assertEqual(human_number(1), u'eins')
        self.assertEqual(human_number(10), u'zehn')
        self.assertEqual(human_number(11), u'elf')
        self.assertEqual(human_number(12), u'zwölf')
        self.assertEqual(human_number(13), 13)
        self.assertEqual(human_number(42), 42)
