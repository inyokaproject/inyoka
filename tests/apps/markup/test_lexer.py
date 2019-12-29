# -*- coding: utf-8 -*-
"""
    tests.apps.markup.test_lexer
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This unittest tests various features of the wiki lexer. Just the lexer,
    not the parser.

    :copyright: (c) 2007-2020 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import unittest

from inyoka.markup.lexer import Lexer

lexer = Lexer()


class TestLexer(unittest.TestCase):

    def test_inline_markup(self):
        expect = lexer.tokenize(
            u"''foo''"
            u"'''foo'''"
            u"__foo__"
            u',,(foo),,'
            u'^^(foo)^^'
            u'--(foo)--'
            u'`foo`'
            u'``foo``'
            u'~-(foo)-~'
            u'~+(foo)+~'
            u'((foo))'
            u'[color=red]foo[/color]'
        ).expect

        for element in ('emphasized', 'strong', 'underline', 'sub', 'sup',
                        'stroke', 'code', 'escaped_code', 'small', 'big',
                        'footnote'):
            expect(element + '_begin')
            expect('text', 'foo')
            expect(element + '_end')

        expect('color_begin')
        expect('color_value', 'red')
        expect('text', 'foo')
        expect('color_end')

        expect('eof')

    def test_extra(self):
        expect = lexer.tokenize(
            u'--------------------\n'
            u'foo'
        ).expect

        expect('ruler')
        expect('text', 'foo')
        expect('eof')

    def test_escape(self):
        expect = lexer.tokenize(
            u'\\__test\\__\\\\foo'
        ).expect

        expect('text', '__test__\\\\foo')
        expect('eof')

    def test_links(self):
        expect = lexer.tokenize(
            u'[:foo:]'
            u'[:foo:bar]'
            u'[foo:bar:baz]'
            u'[?action=edit]'
            u'[http://example.com example]'
            u'[http://example.com] ]'
        ).expect

        expect('wiki_link_begin')
        expect('link_target', (None, 'foo'))
        expect('wiki_link_end')

        expect('wiki_link_begin')
        expect('link_target', (None, 'foo'))
        expect('text', 'bar')
        expect('wiki_link_end')

        expect('wiki_link_begin')
        expect('link_target', ('foo', 'bar'))
        expect('text', 'baz')
        expect('wiki_link_end')

        expect('external_link_begin')
        expect('link_target', '?action=edit')
        expect('external_link_end')

        expect('external_link_begin')
        expect('link_target', 'http://example.com')
        expect('text', 'example')
        expect('external_link_end')

        expect('external_link_begin')
        expect('link_target', 'http://example.com')
        expect('external_link_end')
        expect('text', ' ]')

        expect('eof')

    def test_link_wiki_anchor_simple(self):
        expect = lexer.tokenize(
            u'[:foo#anchor:]'
        ).expect

        expect('wiki_link_begin')
        expect('link_target', (None, 'foo#anchor'))
        expect('wiki_link_end')

        expect('eof')

    def test_link_wiki_anchor_custom_label(self):
        expect = lexer.tokenize(
            u'[:foo#anchor:bar]'
        ).expect

        expect('wiki_link_begin')
        expect('link_target', (None, 'foo#anchor'))
        expect('text', 'bar')
        expect('wiki_link_end')

        expect('eof')

    def test_link_interwiki_custom_label(self):
        expect = lexer.tokenize(
            u'[foo:bar#anchor:baz]'
        ).expect

        expect('wiki_link_begin')
        expect('link_target', ('foo', 'bar#anchor'))
        expect('text', 'baz')
        expect('wiki_link_end')

        expect('eof')

    def test_meta(self):
        expect = lexer.tokenize(
            u'## This is a comment\n'
            u'# This: is metadata'
        ).expect

        expect('metadata_begin')
        expect('metadata_key', 'This')
        expect('text', 'is metadata')
        expect('metadata_end')
        expect('eof')

    def test_pre(self):
        expect = lexer.tokenize(
            u'{{{\nfoo\nbar\n}}}\n'
            u'{{{#!bar foo, blub=blah\nfoo\n}}}'
        ).expect

        expect('pre_begin')
        expect('text', '\nfoo\nbar\n')
        expect('pre_end')

        expect('text', '\n')

        expect('pre_begin')
        expect('parser_begin', 'bar')
        expect('text', 'foo')
        expect('func_argument_delimiter')
        expect('func_kwarg', 'blub')
        expect('text', 'blah')
        expect('parser_end')
        expect('text', '\nfoo\n')
        expect('pre_end')

        expect('eof')

    def test_pre_quote_mixture(self):
        expect = lexer.tokenize('\n'.join((
            u'foo',
            u'{{{',
            u'> foo',
            u'}}}',
            u'bar'
        ))).expect
        expect('text', 'foo\n')
        expect('pre_begin')
        expect('text', '\n> foo\n')
        expect('pre_end')
        expect('text', '\nbar')
        expect('eof')

    def test_table(self):
        expect = lexer.tokenize(
            u'||1||2||3||\n'
            u'||4||5||6||\n\n'
            u'||<42 foo=bar>1||'
        ).expect

        expect('table_row_begin')
        expect('text', '1')
        expect('table_col_switch')
        expect('text', '2')
        expect('table_col_switch')
        expect('text', '3')
        expect('table_row_end')

        expect('table_row_begin')
        expect('text', '4')
        expect('table_col_switch')
        expect('text', '5')
        expect('table_col_switch')
        expect('text', '6')
        expect('table_row_end')

        expect('text', '\n')

        expect('table_row_begin')
        expect('table_def_begin')
        expect('text', '42')
        expect('func_kwarg', 'foo')
        expect('text', 'bar')
        expect('table_def_end')
        expect('text', '1')
        expect('table_row_end')

        expect('eof')

    def test_box(self):
        expect = lexer.tokenize(
            u'{{|\nfoo\n|}}\n'
            u'{{|<1 foo=2>\nfoo\n|}}'
        ).expect

        expect('box_begin')
        expect('text', '\nfoo\n')
        expect('box_end')

        expect('text', '\n')

        expect('box_begin')
        expect('box_def_begin')
        expect('text', '1')
        expect('func_kwarg', 'foo')
        expect('text', '2')
        expect('box_def_end')
        expect('text', '\nfoo\n')
        expect('box_end')

        expect('eof')

    def test_list(self):
        expect = lexer.tokenize(
            ' * foo\n'
            '  * foo\n'
            ' 1. foo\n'
            ' a. foo'
        ).expect

        for x in xrange(4):
            expect('list_item_begin')
            expect('text', 'foo')
            expect('list_item_end')

        expect('eof')

    def test_quote(self):
        expect = lexer.tokenize(
            '> foo\n'
            ">> '''bar\n"
            ">> bar'''\n"
            '> foo'
        ).expect

        expect('quote_begin')
        expect('text', 'foo')
        expect('quote_begin')
        expect('strong_begin')
        expect('text', 'bar\nbar')
        expect('strong_end')
        expect('quote_end')
        expect('text', 'foo')
        expect('quote_end')
        expect('eof')

    def test_broken_old_bbcode_handling(self):
        # See http://log.apolloner.eu/group/151
        expect = lexer.tokenize('[url=http://plangin.de]Plangin.de[/url]').expect
        expect('text', u'[url=')
        expect('free_link', u'http://plangin.de')
        expect('text', u']Plangin.de[/url]')

        expect = lexer.tokenize('[url=http://digital-jockeys.de]Digital Jockeys[/url]').expect
        expect('text', u'[url=')
        expect('free_link', u'http://digital-jockeys.de')
        expect('text', u']Digital Jockeys[/url]')

    def test_basic_unicode_handling(self):
        expect = lexer.tokenize(u'some @¹“”¹unicod€ stuff'.encode('utf-8')).expect
        expect('text', u'some @¹“”¹unicod€ stuff')

    def test_escaped_code(self):
        expect = lexer.tokenize('``text`text``').expect
        expect('escaped_code_begin')
        expect('text', 'text`text')
        expect('escaped_code_end')
        expect('eof')
