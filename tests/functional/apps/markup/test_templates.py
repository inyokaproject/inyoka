#-*- coding: utf-8 -*-
"""
    tests.functional.apps.markup.test_templates
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2007-2013 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from django.test import TestCase
from django.utils import translation

from inyoka.markup import templates


class TestWikiTemplates(TestCase):
    def test_valid_for(self):
        code = '<@ for $l in $list @><@ endfor @>'
        parser = templates.Parser(code)
        for_node = parser.subparse(None)
        self.assertIsInstance(for_node, templates.For)
        self.assertEqual(for_node.var, 'l')
        self.assertEqual(for_node.seq.name, 'list')

    def test_valid_postfix(self):
        code = '<@ $author.groups.1 @>'
        parser = templates.Parser(code)
        node = parser.subparse(None)

        self.assertIsInstance(node, templates.GetItem)
        self.assertEqual(node.item.value, 1.0)

        node = node.expr
        self.assertIsInstance(node, templates.GetItem)
        self.assertEqual(node.item.value, 'groups')

        node = node.expr
        self.assertIsInstance(node, templates.Var)
        self.assertEqual(node.name, 'author')

    def test_invalid_primary(self):
        code = '<@ , $author @>'
        parser = templates.Parser(code)
        with translation.override('en-us'):
            node = parser.subparse(None)
        self.assertIsInstance(node, templates.Data)
        self.assertIn('Unexpected operator', node.markup)

    def test_getitem_on_strings(self):
        context = [('args', ['some_string'])]
        code = '<@ for $arg in $args @><@ $arg.10 @><@ endfor @>'
        self.assertEqual(templates.process(code, context), 'g')

    def test_getitem_numbered(self):
        context = [('arg', 'some_string')]
        code = '<@ $arg.10 @>'
        self.assertEqual(templates.process(code, context), 'g')

    def test_regression_ticket867(self):
        code = '<@ if 1 != 3 @>:)<@ else @>:(<@ endif @>'
        self.assertEqual(templates.process(code), ':)')

    def test_regression_ticket868(self):
        code = '<@ if "foobar" starts_with \'a\' @>true<@ else @>false<@ endif @>'
        self.assertEqual(templates.process(code), 'false')


class TestBinaryFunctions(TestCase):

    def test_contain(self):
        code = '<@ if $a contain $b @>True<@ endif @>'

        context = [('a', 'abc'), ('b', 'b')]
        self.assertEqual(templates.process(code, context), 'True')

        context = [('a', ['a', 'b', 'c']), ('b', 'b')]
        self.assertEqual(templates.process(code, context), 'True')

        context = [('a', [1, 2, 3]), ('b', 'b')]
        self.assertEqual(templates.process(code, context), '')

    def test_contains(self):
        code = '<@ if $a contains $b @>True<@ endif @>'

        context = [('a', 'abc'), ('b', 'b')]
        self.assertEqual(templates.process(code, context), 'True')

        context = [('a', ['a', 'b', 'c']), ('b', 'b')]
        self.assertEqual(templates.process(code, context), 'True')

        context = [('a', [1, 2, 3]), ('b', 'b')]
        self.assertEqual(templates.process(code, context), '')

    def test_has_key(self):
        code = '<@ if $a has_key $b @>True<@ endif @>'

        context = [('a.bar', 'rab'), ('a.buz', 'zub'), ('b', 'bar')]
        self.assertEqual(templates.process(code, context), 'True')

        context = [('a.bar', 'rab'), ('a.buz', 'zub'), ('b', 'lorem')]
        self.assertEqual(templates.process(code, context), '')

    def test_starts_with(self):
        code = '<@ if $a starts_with $b @>True<@ endif @>'

        context = [('a', 'lorem'), ('b', 'lo')]
        self.assertEqual(templates.process(code, context), 'True')

        context = [('a', 'lorem'), ('b', 'ip')]
        self.assertEqual(templates.process(code, context), '')

        context = [('a', 123), ('b', 1)]
        self.assertEqual(templates.process(code, context), 'True')

        context = [('a', 123), ('b', 23)]
        self.assertEqual(templates.process(code, context), '')

    def test_ends_with(self):
        code = '<@ if $a ends_with $b @>True<@ endif @>'

        context = [('a', 'lorem'), ('b', 'em')]
        self.assertEqual(templates.process(code, context), 'True')

        context = [('a', 'lorem'), ('b', 'um')]
        self.assertEqual(templates.process(code, context), '')

        context = [('a', 123), ('b', 3)]
        self.assertEqual(templates.process(code, context), 'True')

        context = [('a', 123), ('b', 12)]
        self.assertEqual(templates.process(code, context), '')

    def test_matches(self):
        code = '<@ if $a matches $b @>True<@ endif @>'

        context = [('a', 'lorem'), ('b', '*re*')]
        self.assertEqual(templates.process(code, context), 'True')

        context = [('a', 'lorem'), ('b', 'lore')]
        self.assertEqual(templates.process(code, context), '')

        context = [('a', "123"), ('b', 123)]
        self.assertEqual(templates.process(code, context), 'True')

        context = [('a', 12.3), ('b', 123)]
        self.assertEqual(templates.process(code, context), '')

    def test_matches_regex(self):
        code = '<@ if $a matches_regex $b @>True<@ endif @>'

        context = [('a', '1234'), ('b', '\d+')]
        self.assertEqual(templates.process(code, context), 'True')

        context = [('a', 'FooBar'), ('b', '[a-z]')]
        self.assertEqual(templates.process(code, context), '')

        context = [('a', 'Fo0Bar'), ('b', '[a-z0-9](?i)')]
        self.assertEqual(templates.process(code, context), 'True')

        context = [('a', 112.34), ('b', 12.3)]
        self.assertEqual(templates.process(code, context), '')

        context = [('a', 112.34), ('b', '.*12.3')]
        self.assertEqual(templates.process(code, context), 'True')

    def test_join_with(self):
        code = '<@ $a join_with $b @>'

        context = [('a', [1, 2, 'a', 'b', 1.2, 3.4]), ('b', ', ')]
        self.assertEqual(templates.process(code, context), '1, 2, a, b, 1.2, 3.4')

    def test_split_by(self):
        code = '<@ ($a split_by $b) join_with "X" @>'

        context = [('a', '1, 2, a, b, 1.2, 3.4'), ('b', ', ')]
        self.assertEqual(templates.process(code, context), '1X2XaXbX1.2X3.4')
