"""
    tests.utils.test_templating
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tests for the Inyoka template filters.

    :copyright: (c) 2011-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import unittest

from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from inyoka.utils.templating import json_filter


class TestTemplating(unittest.TestCase):

    def test_json_encoding(self):

        u = _('text')
        l = gettext_lazy('text')
        t = '"text"'
        self.assertEqual(json_filter(u), t)
        self.assertEqual(json_filter(l), t)

        u = [_('e1'), _('e2')]
        l = [gettext_lazy('e1'), gettext_lazy('e2')]
        t = '["e1", "e2"]'
        self.assertEqual(json_filter(u), t)
        self.assertEqual(json_filter(l), t)

        u = {1: _('v1'), 2: _('v2')}
        l = {1: gettext_lazy('v1'), 2: gettext_lazy('v2')}
        t = '{"1": "v1", "2": "v2"}'
        self.assertEqual(json_filter(u), t)
        self.assertEqual(json_filter(l), t)
