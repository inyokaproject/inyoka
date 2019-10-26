# -*- coding: utf-8 -*-
"""
    tests.apps.markup.test_html_renderer
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Here we test the HTML rendering.

    :copyright: (c) 2013-2019 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import unittest
from django.test import override_settings

from inyoka.markup.base import Parser, RenderContext
from inyoka.utils.urls import href


def render(source):
    """Parse source and render it to html."""
    tree = Parser(source, []).parse()
    html = tree.render(RenderContext(), 'html')
    return html


class TestHtmlRenderer(unittest.TestCase):
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

    def test_topic_link_with_whitespace(self):
        """Test topic link rendering with whitespace in target and describtion."""
        html = render("[topic: with : whitespace ]")
        self.assertEqual(html, (
            '<a href="http://forum.ubuntuusers.local:8080/topic/with/" class="crosslink topic">'
            'whitespace'
            '</a>'
        ))

    def test_wiki_link_with_whitespace(self):
        """Test wiki link rendering with whitespace in target."""
        html = render("[: page :]")
        self.assertEqual(html, (
            '<a href="http://wiki.ubuntuusers.local:8080/page/" class="internal missing">'
            'page'
            '</a>'
        ))

    def test_wikilink_with_anchor_no_description(self):
        html = render('[:foo#anchor:]')

        link = '<a href="{url}" class="internal missing">foo (section \u201canchor\u201d)</a>'
        link = link.format(url=href('wiki', 'foo', _anchor='anchor'))
        self.assertEqual(html, link)

    @override_settings(LANGUAGE_CODE='de-DE')
    def test_localized_wikilink_with_anchor_no_description(self):
        html = render('[:foo#anchor:]')

        link = '<a href="{url}" class="internal missing">foo (Abschnitt \u201eanchor\u201c)</a>'
        link = link.format(url=href('wiki', 'foo', _anchor='anchor'))
        self.assertEqual(html, link)
