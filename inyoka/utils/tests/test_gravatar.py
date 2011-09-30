#-*- coding: utf-8 -*-
from django.test import TestCase
from inyoka.utils.gravatar import get_gravatar


class TestGravatar(TestCase):

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
