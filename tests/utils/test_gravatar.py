#-*- coding: utf-8 -*-
"""
    tests.utils.test_gravatar
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Test some gravatar url creation features.

    :copyright: (c) 2011-2013 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL.
"""
import unittest
from inyoka.utils.gravatar import get_gravatar


class TestGravatar(unittest.TestCase):

    def test_get_gravatar(self):
        self.assertEqual(get_gravatar('gridaphobe@gmail.com'),
                         'http://www.gravatar.com/avatar/16b87da510d278999c892cdbdd55c1b6?s=80&r=g&d=mm')

        self.assertEqual(get_gravatar('gridaphobe@gmail.com', secure=True),
                         'https://secure.gravatar.com/avatar/16b87da510d278999c892cdbdd55c1b6?s=80&r=g&d=mm')

        self.assertEqual(get_gravatar('gridaphobe@gmail.com', rating='pg'),
                         'http://www.gravatar.com/avatar/16b87da510d278999c892cdbdd55c1b6?s=80&r=pg&d=mm')

        self.assertEqual(get_gravatar('gridaphobe@gmail.com', size=250),
                         'http://www.gravatar.com/avatar/16b87da510d278999c892cdbdd55c1b6?s=250&r=g&d=mm')

        self.assertEqual(get_gravatar('gridaphobe@gmail.com', default='retro'),
                         'http://www.gravatar.com/avatar/16b87da510d278999c892cdbdd55c1b6?s=80&r=g&d=retro')
