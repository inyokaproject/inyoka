#-*- coding: utf-8 -*-
from django.test import TestCase
from inyoka.utils.text import get_next_increment


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
