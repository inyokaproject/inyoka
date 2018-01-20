# -*- coding: utf-8 -*-
"""
    tests.apps.markup.test_transformers
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module tests the AST transformers.

    :copyright: Copyright 2007 by Armin Ronacher.
    :copyright: (c) 2011-2018 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import unittest

from inyoka.markup import Parser, nodes, transformers
from inyoka.markup.transformers import (
    AutomaticParagraphs,
    FootnoteSupport,
    HeadlineProcessor,
    get_smiley_re,
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

    def test_smiley_re(self):
        transformers._smiley_re = None
        smileys = {':)': '', ':/': '', '8-o': '', '{de}': ''}
        smiley_re = get_smiley_re(smileys)
        t = lambda x: smiley_re.findall(x)
        self.assertEqual(t(':) :/'), [':)', ':/'])
        self.assertEqual(t('(text:)'), [])
        self.assertEqual(t(':)apo'), [])
        # crazy stuff like that won't work, since smileys aren't
        # allowed to be precised by alphanumeric characters
        # self.assertEqual(t(':)8-o:)'), [':)', '8-o', ':)'])
        # but this should work:
        self.assertEqual(t(':):/'), [':)', ':/'])
        # and so do the language tags:
        self.assertEqual(t('{de}{de}'), ['{de}', '{de}'])
