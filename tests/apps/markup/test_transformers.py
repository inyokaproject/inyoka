# -*- coding: utf-8 -*-
"""
    tests.apps.markup.test_transformers
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module tests the AST transformers.

    :copyright: Copyright 2007 by Armin Ronacher.
    :copyright: (c) 2011-2021 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import unittest
from mock import patch

from inyoka.markup import nodes, transformers
from inyoka.markup.base import Parser
from inyoka.markup.transformers import (
    AutomaticParagraphs,
    FootnoteSupport,
    HeadlineProcessor,
    SmileyInjector
)


def parse(source, transformer):
    """
    Helper function that parses sourcecode with one transformer. Additionally
    it prints the tree so that it appears in the debug output.
    """
    tree = Parser(source, [transformer]).parse()
    return tree


class TestTransformers(unittest.TestCase):

    def test_automatic_paragraphs(self):
        """Test the automatic paragraph insertion."""
        tree = parse("foo\n\nbar ''baz''blub.\n * foo\n{{{\nfoo\n}}}\n\nblub",
                     AutomaticParagraphs())
        self.assertEqual(tree, nodes.Document([
            nodes.Paragraph([nodes.Text('foo')]),
            nodes.Paragraph([
                nodes.Text('bar '),
                nodes.Emphasized([
                    nodes.Text('baz')
                ]),
                nodes.Text('blub.\n')
            ]),
            nodes.List('unordered', [
                nodes.ListItem([nodes.Paragraph([nodes.Text('foo')])])
            ]),
            nodes.Preformatted([
                nodes.Text('foo')
            ], class_='notranslate'),
            nodes.Paragraph([
                nodes.Text('blub')
            ])
        ]))

    def test_footnote_support(self):
        """Check if the footnote support works flawlessly."""
        tree = parse('foo((bar)). bar((baz))', FootnoteSupport())
        self.assertEqual(tree, nodes.Document([
            nodes.Text('foo'),
            nodes.Footnote([nodes.Text('bar')], id=1),
            nodes.Text('. bar'),
            nodes.Footnote([nodes.Text('baz')], id=2),
            nodes.List('unordered', class_='footnotes', children=[
                nodes.ListItem([
                    nodes.Link('#bfn-1', [nodes.Text('1')], id='fn-1'),
                    nodes.Text(': '),   # this is intended behavior
                    nodes.Text('bar')
                ]),
                nodes.ListItem([
                    nodes.Link('#bfn-2', [nodes.Text('2')], id='fn-2'),
                    nodes.Text(': '),   # this is intended behavior
                    nodes.Text('baz')
                ])
            ])
        ]))

    def test_headline_processor(self):
        """Test the headline processing."""
        tree = parse('= foo =\n== foo ==\n== foo-2 ==', HeadlineProcessor())
        self.assertEqual(tree, nodes.Document([
            nodes.Headline(1, [nodes.Text('foo')], id='foo'),
            nodes.Text('\n'),
            nodes.Headline(2, [nodes.Text('foo')], id='foo-2'),
            nodes.Text('\n'),
            nodes.Headline(2, [nodes.Text('foo-2')], id='foo-2-2')
        ]))


class TestSmileyInjector(unittest.TestCase):

    @patch('inyoka.markup.transformers.SmileyInjector.smilies', {':)': '', ':/': '', '8-o': ''})
    def test_smiley_regex(self):
        smiley_re = transformers.SmileyInjector().smiley_re
        t = lambda x: smiley_re.findall(x)

        self.assertEqual(t(':) :/'), [(':)', ''), (':/', '')])

    @patch('inyoka.markup.transformers.SmileyInjector.smilies', {':)': '', ':/': '', '8-o': ''})
    def test_smiley_regex_text_before_smiley(self):
        smiley_re = transformers.SmileyInjector().smiley_re
        t = lambda x: smiley_re.findall(x)

        self.assertEqual(t('(text:)'), [])

    @patch('inyoka.markup.transformers.SmileyInjector.smilies', {':)': '', ':/': '', '8-o': ''})
    def test_smiley_regex_text_after_smiley(self):
        smiley_re = transformers.SmileyInjector().smiley_re
        t = lambda x: smiley_re.findall(x)

        self.assertEqual(t(':)apo'), [])

    @patch('inyoka.markup.transformers.SmileyInjector.smilies', {':)': '', ':/': '', '8-o': ''})
    def test_smiley_regex_no_space_between(self):
        smiley_re = transformers.SmileyInjector().smiley_re
        t = lambda x: smiley_re.findall(x)

        self.assertEqual(t(':):/'), [(':)', ''), (':/', '')])

    @patch('inyoka.markup.transformers.SmileyInjector.smilies', {':)': ''})
    def test_smiley_regex_flags(self):
        smiley_re = transformers.SmileyInjector().smiley_re
        t = lambda x: smiley_re.findall(x)

        self.assertEqual(t('{de}{de}'), [('{de}', 'de'), ('{de}', 'de')])

    @patch('inyoka.markup.transformers.SmileyInjector.smilies', {':)': '☺'})
    def test_smiley_between_text(self):
        tree = parse('blah :) foo', SmileyInjector())
        self.assertEqual(tree, nodes.Document(children=[nodes.Text(text='blah '),
                                                         nodes.Text(text='☺'),
                                                         nodes.Text(text=' foo')]))

    def test_flag_en(self):
        tree = parse('{en}', SmileyInjector())
        self.assertEqual(tree, nodes.Document(children=[nodes.Text(text='🇬🇧')]))

    def test_flag_austria(self):
        tree = parse('{at}', SmileyInjector())
        self.assertEqual(tree, nodes.Document(children=[nodes.Text(text='🇦🇹')]))

    def test_flag_american_samoa(self):
        tree = parse('{as}', SmileyInjector())
        self.assertEqual(tree, nodes.Document(children=[nodes.Text(text='🇦🇸')]))

    @patch('inyoka.markup.transformers.SmileyInjector.smilies', {':tux:': 'css-class:icon-tux'})
    def test_fallback_with_span(self):
        tree = parse(':tux:', SmileyInjector())
        self.assertEqual(tree, nodes.Document(children=[nodes.Span(class_='icon-tux')]))
