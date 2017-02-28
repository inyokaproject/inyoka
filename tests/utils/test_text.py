# -*- coding: utf-8 -*-
"""
    tests.utils.test_utils
    ~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2007-2017 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import unittest

from django.test import override_settings

from inyoka.utils.text import human_number


class TestHumanNumber(unittest.TestCase):
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

    def test_last_text(self):
        self.assertEqual(human_number(12), u'twelve')

    def test_regular_number(self):
        self.assertEqual(human_number(13), 13)

    def test_everything(self):
        self.assertEqual(human_number(42), 42)
