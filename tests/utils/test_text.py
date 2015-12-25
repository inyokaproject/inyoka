# -*- coding: utf-8 -*-
"""
    tests.utils.test_utils
    ~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2007-2016 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import unittest

from inyoka.utils.text import human_number


class TestText(unittest.TestCase):
    def test_human_number(self):
        self.assertEqual(human_number(-1337), -1337)
        self.assertEqual(human_number(0), 0)
        self.assertEqual(human_number(1, 'masculine'), u'one')
        self.assertEqual(human_number(1, 'feminine'), u'one')
        self.assertEqual(human_number(1, 'neuter'), u'one')
        self.assertEqual(human_number(1), u'one')
        self.assertEqual(human_number(10), u'ten')
        self.assertEqual(human_number(11), u'eleven')
        self.assertEqual(human_number(12), u'twelve')
        self.assertEqual(human_number(13), 13)
        self.assertEqual(human_number(42), 42)
