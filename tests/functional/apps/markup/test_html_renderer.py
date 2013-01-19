# -*- coding: utf-8 -*-
"""
    tests.functional.apps.markup.test_html_renderer
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Here we test the HTML rendering.

    :copyright: Copyright 2007 by Armin Ronacher.
    :license: GNU GPL.
"""
from django.test import TestCase

from inyoka.markup import Parser, RenderContext


def render(source):
    """Parse source and render it to html."""
    tree = Parser(source, []).parse()
    html = tree.render(RenderContext(), 'html')
    return html


class TestHtmlRenderer(TestCase):
    def test_simple_markup(self):
        """Test the simple markup."""
        html = render("''foo'', '''bar''', __baz__, ,,(foo),,, ^^(bar)^^")
        self.assertEqual(html, (
            '<em>foo</em>, '
            '<strong>bar</strong>, '
            '<span class="underline">baz</span>, '
            '<sub>foo</sub>, '
            '<sup>bar</sup>'
        ))

    def test_pre(self):
        """Check if pre renders correctly."""
        self.assertEqual(render('{{{\n<em>blub</em>\n}}}'), (
            '<pre class="notranslate">&lt;em&gt;blub&lt;/em&gt;</pre>'
        ))

    def test_lists(self):
        """Check list rendering."""
        html = render(' * 1\n * 2\n  1. 3\n * 4')
        self.assertEqual(html, (
            '<ul>'
              '<li>1</li>'
              '<li>2<ol class="arabic">'
                '<li>3</li>'
              '</ol></li>'
              '<li>4</li>'
            '</ul>'
        ))

    def test_blockquotes(self):
        """Test block quote rendering."""
        html = render("> ''foo\n> bar''\n>> nested")
        self.assertEqual(html, (
            '<blockquote>'
              '<em>foo\nbar</em>'
              '<blockquote>nested</blockquote>'
            '</blockquote>'
        ))
