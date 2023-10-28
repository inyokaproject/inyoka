"""
    tests.utils.test_gravatar
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Test some gravatar url creation features.

    :copyright: (c) 2011-2023 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from inyoka.utils.gravatar import get_gravatar
from inyoka.utils.test import TestCase


class TestGravatar(TestCase):

    def test_get_gravatar(self):
        self.assertURLEqual(get_gravatar('gridaphobe@gmail.com'),
                            'https://www.gravatar.com/avatar/16b87da510d278999c892cdbdd55c1b6?s=80&r=g&d=mm')

        self.assertURLEqual(get_gravatar('gridaphobe@gmail.com', rating='pg'),
                            'https://www.gravatar.com/avatar/16b87da510d278999c892cdbdd55c1b6?s=80&r=pg&d=mm')

        self.assertURLEqual(get_gravatar('gridaphobe@gmail.com', size=250),
                            'https://www.gravatar.com/avatar/16b87da510d278999c892cdbdd55c1b6?s=250&r=g&d=mm')

        self.assertURLEqual(get_gravatar('gridaphobe@gmail.com', default='retro'),
                            'https://www.gravatar.com/avatar/16b87da510d278999c892cdbdd55c1b6?s=80&r=g&d=retro')
