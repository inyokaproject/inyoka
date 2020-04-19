# -*- coding: utf-8 -*-
"""
    tests.utils.test_utils
    ~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2007-2020 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from inyoka.utils.html import cleanup_html, replace_entities
from inyoka.utils.test import TestCase


class TestHTML(TestCase):

    def test_cleanup_html(self):
        self.assertEqual(cleanup_html('Foo Bar'), u'<p>Foo Bar</p>')
        self.assertEqual(cleanup_html('<p>Foo Bar'), u'<p>Foo Bar</p>')
        self.assertEqual(cleanup_html('Foo Bar</p>'), u'<p>Foo Bar</p>')
        self.assertEqual(cleanup_html('<p>Foo Bar</p>'), u'<p>Foo Bar</p>')

        self.assertEqual(cleanup_html('Foo Bar', make_xhtml=True), u'<p>Foo Bar</p>')
        self.assertEqual(cleanup_html('<p>Foo Bar', make_xhtml=True), u'<p>Foo Bar</p>')
        self.assertEqual(cleanup_html('Foo Bar</p>', make_xhtml=True), u'<p>Foo Bar</p>')
        self.assertEqual(cleanup_html('<p>Foo Bar</p>', make_xhtml=True), u'<p>Foo Bar</p>')

        self.assertEqual(cleanup_html('<img src=foo_bar.png>'), u'<img src="foo_bar.png">')
        self.assertEqual(cleanup_html('<img src="foo_bar.png">'), u'<img src="foo_bar.png">')
        self.assertEqual(cleanup_html("<img src='foo_bar.png'>"), u'<img src="foo_bar.png">')

        self.assertEqual(cleanup_html('<img src=foo_bar.png>', make_xhtml=True), u'<img src="foo_bar.png" />')
        self.assertEqual(cleanup_html('<img src="foo_bar.png">', make_xhtml=True), u'<img src="foo_bar.png" />')
        self.assertEqual(cleanup_html("<img src='foo_bar.png'>", make_xhtml=True), u'<img src="foo_bar.png" />')

    def test_replace_entities(self):
        self.assertEqual(replace_entities('foo &amp; bar &raquo; foo'), u'foo & bar \xbb foo')
        self.assertEqual(replace_entities('foo &amp;amp; bar'), u'foo &amp; bar')
