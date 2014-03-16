#-*- coding: utf-8 -*-
"""
    tests.apps.markup.test_css
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2007-2014 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import unittest

from inyoka.markup.utils import filter_style


class TestUtilsCss(unittest.TestCase):
    def test_unwanted_css_properties(self):
        """Test for some xss wholes."""
        self.assertEqual(filter_style(u'background-image: url(javascript: alert("foo"));'), u'')
        self.assertEqual(filter_style(u'-moz-binding: url("http://foobar.xy");'), u'')
        # this makes the ie corrupt and confusing…
        self.assertEqual(filter_style(u'width: expression((documentElement.clientWidth < 725) ? "725px" : "auto" )'), u'')
        # and this is also known to be a security risk in internet explorer
        self.assertEqual(filter_style(u'behavior: url("pngbehavior.htc");'), u'')
