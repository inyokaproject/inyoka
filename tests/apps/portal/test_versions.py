# -*- coding: utf-8 -*-
"""
    tests.apps.portal.test_versions
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tests for the :class:`UbuntuVersion` class, such as ordering.

    :copyright: (c) 2007-2021 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import unittest

from inyoka.portal.utils import UbuntuVersion


class TestVersions(unittest.TestCase):

    def setUp(self):
        self.versions = [
            UbuntuVersion('5.04', 'Hoary Hedgehog'),
            UbuntuVersion('10.10', 'Maverick Meerkat', active=True),
            UbuntuVersion('10.04', 'Lucid Lynx', lts=True, active=True),
            UbuntuVersion('6.06', 'Drapper Drake', lts=True),
            UbuntuVersion('12.04', 'Precise Pangolin', lts=True, dev=True),
            UbuntuVersion('6.10', 'Edgy Eft')]

    def test_order(self):
        """Test the ability of the UbuntuVersion class to sort itself.

        The UbuntuVersion class supports ordering by the
        :py:attr:`inyoka.portal.utils.UbuntuVersion.number` attribute, test
        here if this ordering is correctly done.
        """
        order = ['5.04', '6.06', '6.10', '10.04', '10.10', '12.04']
        versions = [v.number for v in sorted(self.versions)]
        self.assertEqual(order, versions)
