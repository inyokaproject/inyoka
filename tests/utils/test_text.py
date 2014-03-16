# -*- coding: utf-8 -*-
"""
    tests.utils.test_utils
    ~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2007-2014 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL.
"""
import unittest

from django.test import TestCase

from inyoka.utils.text import human_number


class TestText(unittest.TestCase):
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
