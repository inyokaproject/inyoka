# -*- coding: utf-8 -*-
"""
    tests.utils.test_templating
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tests for the Inyoka template filters.

    :copyright: (c) 2011-2023 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import unittest

from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy

from inyoka.utils.templating import json_filter


class TestTemplating(unittest.TestCase):

    def test_json_encoding(self):

        u = _('text')
        l = ugettext_lazy('text')
        t = '"text"'
        self.assertEqual(json_filter(u), t)
        self.assertEqual(json_filter(l), t)

        u = [_('e1'), _('e2')]
        l = [ugettext_lazy('e1'), ugettext_lazy('e2')]
        t = '["e1", "e2"]'
        self.assertEqual(json_filter(u), t)
        self.assertEqual(json_filter(l), t)

        u = {1: _('v1'), 2: _('v2')}
        l = {1: ugettext_lazy('v1'), 2: ugettext_lazy('v2')}
        t = '{"1": "v1", "2": "v2"}'
        self.assertEqual(json_filter(u), t)
        self.assertEqual(json_filter(l), t)
