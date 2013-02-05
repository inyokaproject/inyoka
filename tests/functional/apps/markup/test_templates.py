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
