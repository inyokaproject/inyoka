# -*- coding: utf-8 -*-
"""
    tests.utils.test_utils
    ~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2007-2013 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL.
"""
from django.test import TestCase
from inyoka.utils.html import cleanup_html, replace_entities


class TestHTML(TestCase):

    def test_cleanup_html(self):
        self.assertEqual(cleanup_html('Foo Bar'), u'<p>Foo Bar</p>')
        self.assertEqual(cleanup_html('<p>Foo Bar'), u'<p>Foo Bar</p>')
        self.assertEqual(cleanup_html('Foo Bar</p>'), u'<p>Foo Bar</p>')
        self.assertEqual(cleanup_html('<p>Foo Bar</p>'), u'<p>Foo Bar</p>')

        self.assertEqual(cleanup_html('<img src=foo_bar.png>'), u'<img src="foo_bar.png">')
        self.assertEqual(cleanup_html('<img src="foo_bar.png">'), u'<img src="foo_bar.png">')
        self.assertEqual(cleanup_html("<img src='foo_bar.png'>"), u'<img src="foo_bar.png">')

    def test_replace_entities(self):
        self.assertEqual(replace_entities('foo &amp; bar &raquo; foo'), u'foo & bar \xbb foo')
        self.assertEqual(replace_entities('foo &amp;amp; bar'), u'foo &amp; bar')
