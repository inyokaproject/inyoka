"""
    tests.apps.markup.test_css
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2007-2025 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import unittest

from inyoka.markup.utils import filter_style


class TestUtilsCss(unittest.TestCase):
    def test_unwanted_css_properties(self):
        """Test for some xss wholes."""
        self.assertEqual(filter_style('background-image: url(javascript: alert("foo"));'), '')
        self.assertEqual(filter_style('-moz-binding: url("http://foobar.xy");'), '')
        # this makes the ie corrupt and confusing…
        self.assertEqual(filter_style('width: expression((documentElement.clientWidth < 725) ? "725px" : "auto" )'), '')
        # and this is also known to be a security risk in internet explorer
        self.assertEqual(filter_style('behavior: url("pngbehavior.htc");'), '')

        self.assertEqual(filter_style('background: foobar;'), '')

    def test_valid_css_properties(self):
        self.assertEqual(filter_style('voice-family: yellow;'), 'voice-family: yellow')
        self.assertEqual(filter_style('background: yellow;'), 'background: yellow')
        self.assertEqual(filter_style('background: yellow; voice-family: yellow;'), 'background: yellow; voice-family: yellow')

