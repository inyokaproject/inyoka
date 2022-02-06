# -*- coding: utf-8 -*-
"""
    tests.apps.markup.test_parser
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This unittests tests the parser.

    :copyright: Copyright 2007 by Armin Ronacher.
    :copyright: (c) 2011-2022 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import unittest

from inyoka.markup import nodes
from inyoka.markup.base import Parser
from inyoka.portal.models import Linkmap
from inyoka.markup.nodes import InterWikiLink
from inyoka.utils.urls import href


def parse(code):
    """
    Simple parsing function that doesn't use any transformers. This also
    prints the tree for easier debugging.
    """
    tree = Parser(code, transformers=[]).parse()
    return tree


class TestParser(unittest.TestCase):

    def test_inline_formattings(self):
        """Simple test for some inline formattings."""
        tree = parse("''baz'' but '''foo''' and __bar__.")
        self.assertEqual(tree, nodes.Document([
            nodes.Emphasized([
                nodes.Text('baz')
            ]),
            nodes.Text(' but '),
            nodes.Strong([
                nodes.Text('foo')
            ]),
            nodes.Text(' and '),
            nodes.Underline([
                nodes.Text('bar')
            ]),
            nodes.Text('.')
        ]))

    def test_escaping(self):
        """Check if escaping works properly."""
        tree = parse("\\__bar\\__")
        self.assertEqual(tree, nodes.Document([
            nodes.Text("__bar__")
        ]))

    def test_autoclosing(self):
        """Check if the automatic closing works."""
        tree = parse("''foo __bar")
        self.assertEqual(tree, nodes.Document([
            nodes.Emphasized([
                nodes.Text('foo '),
                nodes.Underline([
                    nodes.Text('bar')
                ])
            ])
        ]))

    def test_simple_lists(self):
        """Check if simple lists work."""
        tree = parse(' * foo\n * ^^(bar)^^\n * ,,(baz),,')
        self.assertEqual(tree, nodes.Document([
            nodes.List('unordered', [
                nodes.ListItem([nodes.Text('foo')]),
                nodes.ListItem([
                    nodes.Sup([nodes.Text('bar')])
                ]),
                nodes.ListItem([
                    nodes.Sub([nodes.Text('baz')])
                ])
            ])
        ]))

    def test_nested_lists(self):
        """Check if nested lists work."""
        tree = parse(' * foo\n  1. bar\n   a. baz\n * blub')
        self.assertEqual(tree, nodes.Document([
            nodes.List('unordered', [
                nodes.ListItem([
                    nodes.Text('foo'),
                    nodes.List('arabic', [
                        nodes.ListItem([
                            nodes.Text('bar'),
                            nodes.List('alphalower', [
                                nodes.ListItem([nodes.Text('baz')])
                            ])
                        ])
                    ])
                ]),
                nodes.ListItem([nodes.Text('blub')])
            ])
        ]))

    def test_simple_table(self):
        """Test the simple table markup."""
        tree = parse('||1||2||3||\n||4||5||6||')
        self.assertEqual(tree, nodes.Document([
            nodes.Table([
                nodes.TableRow([
                    nodes.TableCell([nodes.Text('1')]),
                    nodes.TableCell([nodes.Text('2')]),
                    nodes.TableCell([nodes.Text('3')])
                ]),
                nodes.TableRow([
                    nodes.TableCell([nodes.Text('4')]),
                    nodes.TableCell([nodes.Text('5')]),
                    nodes.TableCell([nodes.Text('6')])
                ])
            ])
        ]))

    def test_span_table(self):
        """Test tables with col/rowspans."""
        tree = parse('||<-2>1||<|2>2||\n||3||4||')
        self.assertEqual(tree, nodes.Document([
            nodes.Table([
                nodes.TableRow([
                    nodes.TableCell([nodes.Text('1')], colspan=2),
                    nodes.TableCell([nodes.Text('2')], rowspan=2)
                ]),
                nodes.TableRow([
                    nodes.TableCell([nodes.Text('3')]),
                    nodes.TableCell([nodes.Text('4')])
                ])
            ])
        ]))

    def test_table_row_classes(self):
        """Test the table row class assignments."""
        tree = parse('||<foo>1||2||3')
        self.assertEqual(tree, nodes.Document([
            nodes.Table([
                nodes.TableRow([
                    nodes.TableCell([nodes.Text('1')]),
                    nodes.TableCell([nodes.Text('2')]),
                    nodes.TableCell([nodes.Text('3')])
                ], class_='foo')
            ])
        ]))

    def test_table_cell_classes(self):
        """Test the table cell classes."""
        tree = parse('||<cellclass=foo>1||<bar>2||')
        self.assertEqual(tree, nodes.Document([
            nodes.Table([
                nodes.TableRow([
                    nodes.TableCell([nodes.Text('1')], class_='foo'),
                    nodes.TableCell([nodes.Text('2')], class_='bar')
                ])
            ])
        ]))

    def test_table_alignment(self):
        """Check if table alignment parameters work."""
        tree = parse('||<:~>1||<(v>2||<)^>3||')
        self.assertEqual(tree, nodes.Document([
            nodes.Table([
                nodes.TableRow([
                    nodes.TableCell([nodes.Text('1')], align='center', valign='middle'),
                    nodes.TableCell([nodes.Text('2')], align='left', valign='bottom'),
                    nodes.TableCell([nodes.Text('3')], align='right', valign='top')
                ])
            ])
        ]))

    def test_pre(self):
        """Test normal pre blocks."""
        tree = parse('{{{\nfoo\n}}}')
        self.assertEqual(tree, nodes.Document([
            nodes.Preformatted([nodes.Text('foo')], class_='notranslate')
        ]))

    def test_breakers(self):
        """Test the ruler."""
        tree = parse('foo\n-----------------')
        self.assertEqual(tree, nodes.Document([
            nodes.Text('foo\n'),
            nodes.Ruler()
        ]))

    def test_wiki_links(self):
        """Test all kinds of wiki links."""
        tree = parse('[:foo:][:foo:bar][foo:bar:][foo:bar:baz]')
        self.assertEqual(tree, nodes.Document([
            nodes.InternalLink('foo'),
            nodes.InternalLink('foo', [nodes.Text('bar')]),
            nodes.InterWikiLink('foo', 'bar'),
            nodes.InterWikiLink('foo', 'bar', [nodes.Text('baz')])
        ]))

    def test_external_links(self):
        """Test all kind of external links."""
        tree = parse('[http://example.org :blub:][?action=edit][http://[bla]')
        self.assertEqual(tree, nodes.Document([
            nodes.Link('http://example.org', [nodes.Text(':blub:')]),
            nodes.Link('?action=edit'), nodes.Link('http://[bla')
        ]))

    def test_interwiki_links(self):
        """Test external interwiki links."""
        Linkmap.objects.create(token=u'github', url=u'https://github.test/')
        Linkmap.objects.create(token=u'page', url=u'https://PAGE.test/')

        iwl = InterWikiLink(u'github', u'inyokaproject')
        iwl.prepare_html()
        self.assertEqual(iwl.resolve_interwiki_link(),
                         u'https://github.test/inyokaproject')

        iwl = InterWikiLink(u'not_existing', u'foo')
        self.assertIsNone(iwl.resolve_interwiki_link())

        iwl = InterWikiLink(u'user', u'foo')
        self.assertEqual(iwl.resolve_interwiki_link(), href('portal', 'user', u'foo'))

        iwl = InterWikiLink(u'attachment', u'foo')
        self.assertEqual(iwl.resolve_interwiki_link(), href('wiki', '_attachment', target=u'foo'))

        iwl = InterWikiLink(u'page', u'foo')
        self.assertEqual(iwl.resolve_interwiki_link(), u'https://foo.test/')

