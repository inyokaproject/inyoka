# -*- coding: utf-8 -*-
"""
    tests.apps.markup.test_html_renderer
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Here we test the HTML rendering.

    :copyright: (c) 2013-2020 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.test import override_settings

from inyoka.markup.base import Parser, RenderContext
from inyoka.markup.transformers import SmileyInjector
from inyoka.utils.test import TestCase
from inyoka.utils.urls import href


def render(source, transformers=None):
    """Parse source and render it to html."""
    if not transformers:
        transformers = []
    tree = Parser(source, transformers).parse()
    html = tree.render(RenderContext(), 'html')
    return html


def render_smilies(source):
    return render(source, [SmileyInjector()])


class TestHtmlRenderer(TestCase):
    def test_simple_markup(self):
        """Test the simple markup."""
        html = render("''foo'', '''bar''', __baz__, ,,(foo),,, ^^(bar)^^")
        self.assertHTMLEqual(html, (
            '<em>foo</em>, '
            '<strong>bar</strong>, '
            '<span class="underline">baz</span>, '
            '<sub>foo</sub>, '
            '<sup>bar</sup>'
        ))

    def test_pre(self):
        """Check if pre renders correctly."""
        self.assertHTMLEqual(render('{{{\n<em>blub</em>\n}}}'), (
            '<pre class="notranslate">&lt;em&gt;blub&lt;/em&gt;</pre>'
        ))

    def test_code_highlight(self):
        html = render("""{{{#!code bash
#!/bin/bash
cp ~/.bash_profile ~/.bash_profile.back

# autologin for user instead of root
sed -i 's/root/arch/' $HOME/.bash_profile
}}}""")
        self.maxDiff = None
        self.assertHTMLEqual(html, """<div class="code">
        <table class="notranslate syntaxtable"><tr><td class="linenos"><div class="linenodiv"><pre>
        <span class="normal">
        1
        </span><span class="normal">
        2
        </span><span class="normal">
        3
        </span><span class="normal">
        4
        </span><span class="normal">
        5
        </span>
        </pre></div></td><td class="code"><div class="notranslate syntax"><pre><span></span><span class="ch">#!/bin/bash</span>
        cp ~/.bash_profile ~/.bash_profile.back

        <span class="c1"># autologin for user instead of root</span>
        sed -i <span class="s1">&39;s/root/arch/&39;</span> <span class="nv">$HOME</span>/.bash_profile
        </pre></div>
        </td></tr></table></div>""")

    def test_csv_to_table(self):
        html = render("""{{{#!csv
Device,Clicks,Impressions,CTR,Position
Desktop,12167283,120602930,10.09%,14.28
Mobile,899256,20140779,4.46%,19.78
Tablet,167759,1843644,9.1%,8.63
}}}""")
        self.assertHTMLEqual(html, """<table>
        <tr><td>Device</td><td>Clicks</td><td>Impressions</td><td>CTR</td><td>Position</td></tr>
        <tr><td>Desktop</td><td>12167283</td><td>120602930</td><td>10.09%</td><td>14.28</td></tr>
        <tr><td>Mobile</td><td>899256</td><td>20140779</td><td>4.46%</td><td>19.78</td></tr>
        <tr><td>Tablet</td><td>167759</td><td>1843644</td><td>9.1%</td><td>8.63</td></tr>
        </table>""")

    def test_invalid_parser(self):
        html = render("{{{#!not_existing_parser_1233456767867899789\ncONTENT}}}")
        self.assertHTMLEqual(html, '<pre class="notranslate">cONTENT</pre>')

    def test_lists(self):
        """Check list rendering."""
        html = render(' * 1\n * 2\n  1. 3\n * 4')
        self.assertHTMLEqual(html, (
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
        self.assertHTMLEqual(html, (
            '<blockquote>'
            '<em>foo\nbar</em>'
            '<blockquote>nested</blockquote>'
            '</blockquote>'
        ))

    def test_topic_link_with_whitespace(self):
        """Test topic link rendering with whitespace in target and describtion."""
        html = render("[topic: with : whitespace ]")
        self.assertHTMLEqual(html, (
            '<a href="http://forum.ubuntuusers.local:8080/topic/with/" class="crosslink topic">'
            'whitespace'
            '</a>'
        ))

    def test_wiki_link_with_whitespace(self):
        """Test wiki link rendering with whitespace in target."""
        html = render("[: page :]")
        self.assertHTMLEqual(html, (
            '<a href="http://wiki.ubuntuusers.local:8080/page/" class="internal missing">'
            'page'
            '</a>'
        ))

    def test_wikilink_with_anchor_no_description(self):
        html = render('[:foo#anchor:]')

        link = '<a href="{url}" class="internal missing">foo (section \u201canchor\u201d)</a>'
        link = link.format(url=href('wiki', 'foo', _anchor='anchor'))
        self.assertHTMLEqual(html, link)

    @override_settings(LANGUAGE_CODE='de-DE')
    def test_localized_wikilink_with_anchor_no_description(self):
        html = render('[:foo#anchor:]')

        link = '<a href="{url}" class="internal missing">foo (Abschnitt \u201eanchor\u201c)</a>'
        link = link.format(url=href('wiki', 'foo', _anchor='anchor'))
        self.assertHTMLEqual(html, link)

    def test_heading_contains_arrow(self):
        html = render_smilies('= => g =')
        self.assertHTMLEqual(html, u'<h2 id="g">\u21d2 g<a href="#g" class="headerlink">\xb6</a></h2>')

    def test_arrows(self):
        html = render_smilies('a => this')
        self.assertHTMLEqual(html, u'a \u21d2 this')

    def test_list_with_arrow(self):
        html = render_smilies(' - -> this')
        self.assertHTMLEqual(html, u'<ul><li>\u2192 this</li></ul>')

    def test_strikethrough_with_dash(self):
        html = render_smilies('a -- --(dvdfv)--')
        self.assertHTMLEqual(html, u'a \u2013 <del>dvdfv</del>')

    def test_arrow_in_bracket(self):
        html = render_smilies('(-> d)')
        self.assertHTMLEqual(html, u'(\u2192 d)')

    def test_compile(self):
        """
        Test alternative way to render with compile.
        See __init__.py for more information.
        """
        from inyoka.markup.base import parse, render
        node = parse("Hello World!\n\n''foo bar spam''")
        code = node.compile('html')
        html = render(code, RenderContext())
        self.assertHTMLEqual(html,
                             '<p>Hello World!</p><p><em>foo bar spam</em></p>')
