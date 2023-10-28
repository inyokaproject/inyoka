"""
    tests.apps.markup.test_templates
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2007-2023 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import unittest

from django.utils import translation

from inyoka.markup import templates
from inyoka.markup.templates import NoneValue, Value


class TestWikiTemplates(unittest.TestCase):
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

    def test_regression_ticket866(self):
        code = '<@ if 5 == 3 @>0<@ elseif 5 == 5 @>1<@ else @>'\
               '<@ if 2 == 3 @>1.5<@ endif @>2<@ endif @>'
        self.assertEqual(templates.process(code), '1')

    def test_regression_ticket867(self):
        code = '<@ if 1 != 3 @>:)<@ else @>:(<@ endif @>'
        self.assertEqual(templates.process(code), ':)')

    def test_regression_ticket868(self):
        code = '<@ if "foobar" starts_with \'a\' @>true<@ else @>false<@ endif @>'
        self.assertEqual(templates.process(code), 'false')

    def test_regression_ticket869(self):
        code = '<@ for $var in [\'a\', \'b\', \'c\'] @><@ $var @><@ endfor @>'
        ret = templates.process(code)
        self.assertEqual(ret, 'abc')

        code = '<@ if $args is array @><@ for $var in $args @><@ $var @><@ endfor @><@ endif @>'
        context = [('args', ['a', 'b', 'c'])]
        ret = templates.process(code, context)
        self.assertEqual(ret, 'abc')

        code = '<@ for $var in [0 => \'a\', 1 => \'b\', 2 => \'c\'] @><@ $var.value @><@ endfor @>'
        ret = templates.process(code)
        self.assertEqual(sorted(ret), ['a', 'b', 'c'])

        code = '<@ for $var in [0 => \'a\', 1 => \'b\', 2 => \'c\'] @><@ $var.key as int @><@ endfor @>'
        ret = templates.process(code)
        self.assertEqual(sorted(ret), ['0', '1', '2'])


class TestValue(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.int1 = Value(42)
        cls.int2 = Value(23)
        cls.float1 = Value(8.15)
        cls.float2 = Value(13.37)
        cls.string1 = Value('lorem')
        cls.string2 = Value('ipsum')
        cls.list1 = Value([Value(1), Value('str'), Value(1.2)])
        cls.list2 = Value([Value(5), Value('unicode'), Value(11.47)])
        cls.tuple1 = Value((Value(1), Value('str'), Value(1.2)))
        cls.tuple2 = Value((Value(5), Value('unicode'), Value(11.47)))
        cls.dict1 = Value({'a': Value('A'), 'b': Value(2), 'c': Value(2.3)})
        cls.dict2 = Value({'d': Value('D'), 'e': Value(6), 'f': Value(9.8)})

    def test_nonzero(self):
        self.assertTrue(bool(self.int1))
        self.assertTrue(bool(self.float1))
        self.assertTrue(bool(self.string1))
        self.assertTrue(bool(self.list1))
        self.assertTrue(bool(self.tuple1))
        self.assertTrue(bool(self.dict1))

        self.assertFalse(bool(Value(None)))
        self.assertFalse(bool(Value(0)))
        self.assertFalse(bool(Value(0.0)))
        self.assertFalse(bool(Value('')))
        self.assertFalse(bool(Value('0')))
        self.assertFalse(bool(Value('0.0')))
        self.assertFalse(bool(Value([])))
        self.assertFalse(bool(Value(())))
        self.assertFalse(bool(Value({})))

    def test_convert(self):
        self.assertEqual(int(self.int1), 42)
        self.assertEqual(int(self.float1), 8)
        self.assertEqual(int(self.string1), 0)
        self.assertEqual(int(self.list1), 0)
        self.assertEqual(int(self.tuple1), 0)
        self.assertEqual(int(self.dict1), 0)

        self.assertEqual(float(self.int1), 42.0)
        self.assertEqual(float(self.float1), 8.15)
        self.assertEqual(float(self.string1), 0.0)
        self.assertEqual(float(self.list1), 0.0)
        self.assertEqual(float(self.tuple1), 0.0)
        self.assertEqual(float(self.dict1), 0.0)

        self.assertEqual(str(self.int1), '42')
        self.assertEqual(str(self.float1), '8.15')
        self.assertEqual(str(self.string1), 'lorem')
        self.assertEqual(str(self.list1), '1, str, 1.2')
        self.assertEqual(str(self.tuple1), '1, str, 1.2')
        # TODO: Can we reliably test the next line?
        # self.assertEqual(unicode(self.dict1), u'a: A, c: 2.3, b: 2')

        self.assertEqual(str(self.int1), '42')
        self.assertEqual(str(self.float1), '8.15')
        self.assertEqual(str(self.string1), 'lorem')
        self.assertEqual(str(self.list1), '1, str, 1.2')
        self.assertEqual(str(self.tuple1), '1, str, 1.2')
        # TODO: Can we reliably test the next line?
        # self.assertEqual(str(self.dict1), 'a: A, c: 2.3, b: 2')

    def test_list(self):
        self.assertEqual(len(self.int1), 0)
        self.assertEqual(len(self.float1), 0)
        self.assertEqual(len(self.string1), 5)
        self.assertEqual(len(self.list1), 3)
        self.assertEqual(len(self.tuple1), 3)
        self.assertEqual(len(self.dict1), 3)

        self.assertEqual(list(iter(self.int1)), [])
        self.assertEqual(list(iter(self.float1)), [])
        self.assertEqual(list(iter(self.string1)), ['l', 'o', 'r', 'e', 'm'])
        self.assertEqual(list(iter(self.list1)), [Value(1), Value('str'), Value(1.2)])
        self.assertEqual(list(iter(self.tuple1)), [Value(1), Value('str'), Value(1.2)])
        # TODO: Can we reliably test the next lines?
        # self.assertEqual(list(iter(self.dict1)), [
        #     Value({'key': 'a', 'value': Value('A')}),
        #     Value({'key': 'c', 'value': Value(2.3)}),
        #     Value({'key': 'b', 'value': Value(2)})
        # ])

    def test_getter(self):
        self.assertEqual(self.int1[1], NoneValue)
        self.assertEqual(self.float1[1], NoneValue)
        self.assertEqual(self.string1[1], 'o')
        self.assertEqual(self.list1[1], Value('str'))
        self.assertEqual(self.tuple1[1], Value('str'))
        self.assertEqual(self.dict1[1], NoneValue)
        self.assertEqual(self.dict1['a'], Value('A'))

    def test_compare(self):
        self.assertEqual(self.int1, Value(42))
        self.assertEqual(self.float1, Value(8.15))
        self.assertEqual(self.string1, Value('lorem'))
        self.assertEqual(self.list1, Value([Value(1), Value('str'), Value(1.2)]))
        self.assertEqual(self.tuple1, Value((Value(1), Value('str'), Value(1.2))))
        self.assertEqual(self.dict1, Value({'a': Value('A'), 'b': Value(2), 'c': Value(2.3)}))

        self.assertNotEqual(self.int1, self.int2)
        self.assertNotEqual(self.float1, self.float2)
        self.assertNotEqual(self.string1, self.string2)
        self.assertNotEqual(self.list1, self.list2)
        self.assertNotEqual(self.tuple1, self.tuple2)
        self.assertNotEqual(self.dict1, self.dict2)

        self.assertEqual(self.int1, self.int1)
        self.assertTrue(self.int1 > self.int2)
        self.assertEqual(self.float1, self.float1)
        self.assertTrue(self.float1 < self.float2)
        self.assertNotEqual(self.string1, self.string2)
        self.assertNotEqual(self.list1, self.list2)
        self.assertNotEqual(self.tuple1, self.tuple2)
        self.assertNotEqual(self.dict1, self.dict2)

    def test_math(self):
        self.assertEqual(self.int1 + self.int2, Value(65))
        self.assertEqual(self.float1 + self.float2, Value(21.52))
        self.assertEqual(self.string1 + self.string2, Value('loremipsum'))
        self.assertEqual(self.list1 + self.list2, Value([Value(1), Value('str'), Value(1.2), Value(5), Value('unicode'), Value(11.47)]))
        self.assertEqual(self.tuple1 + self.tuple2, Value([Value(1), Value('str'), Value(1.2), Value(5), Value('unicode'), Value(11.47)]))
        self.assertEqual(self.dict1 + self.dict2, Value({'a': Value('A'), 'b': Value(2), 'c': Value(2.3), 'd': Value('D'), 'e': Value(6), 'f': Value(9.8)}))

        self.assertEqual(self.int1 - self.int2, Value(19))
        self.assertEqual(self.float1 - self.float2, Value(-5.219999999999999))
        self.assertEqual(self.string1 - self.string2, NoneValue)
        self.assertEqual(self.list1 - self.list2, NoneValue)
        self.assertEqual(self.tuple1 - self.tuple2, NoneValue)
        self.assertEqual(self.dict1 - self.dict2, NoneValue)

        self.assertEqual(self.int1 * self.int2, Value(966))
        self.assertEqual(self.float1 * self.float2, Value(108.96549999999999))
        self.assertEqual(self.string1 * self.string2, NoneValue)
        self.assertEqual(self.list1 * self.list2, NoneValue)
        self.assertEqual(self.tuple1 * self.tuple2, NoneValue)
        self.assertEqual(self.dict1 * self.dict2, NoneValue)

        self.assertEqual(self.int1 / self.int2, Value(1.826086956521739))
        self.assertAlmostEqual((self.float1 / self.float2).value, 0.6095737)
        self.assertEqual(self.string1 / self.string2, NoneValue)
        self.assertEqual(self.list1 / self.list2, NoneValue)
        self.assertEqual(self.tuple1 / self.tuple2, NoneValue)
        self.assertEqual(self.dict1 / self.dict2, NoneValue)

        self.assertEqual(self.int1 % self.int2, Value(19))
        self.assertEqual(self.float1 % self.float2, Value(8.15))
        self.assertEqual(self.string1 % self.string2, NoneValue)
        self.assertEqual(self.list1 % self.list2, NoneValue)
        self.assertEqual(self.tuple1 % self.tuple2, NoneValue)
        self.assertEqual(self.dict1 % self.dict2, NoneValue)

        self.assertEqual(self.int1 & self.int2, Value("4223"))
        self.assertEqual(self.float1 & self.float2, Value("8.1513.37"))
        self.assertEqual(self.string1 & self.string2, Value("loremipsum"))
        self.assertEqual(self.list1 & self.list2, Value("1, str, 1.25, unicode, 11.47"))
        self.assertEqual(self.tuple1 & self.tuple2, Value("1, str, 1.25, unicode, 11.47"))
        # TODO: Can we reliably test the next line?
        # self.assertEqual(self.dict1 & self.dict2, Value("a: A, c: 2.3, b: 2e: 6, d: D, f: 9.8"))

    def test_boolean(self):
        self.assertIn(Value('str'), self.list1)
        self.assertNotIn(Value('foo'), self.list1)
        self.assertIn(Value('str'), self.tuple1)
        self.assertNotIn(Value('foo'), self.tuple1)
        self.assertIn('a', self.dict1)
        self.assertNotIn('xyz', self.dict1)

        self.assertFalse(self.int1.is_string)
        self.assertFalse(self.float1.is_string)
        self.assertTrue(self.string1.is_string)
        self.assertFalse(self.list1.is_string)
        self.assertFalse(self.tuple1.is_string)
        self.assertFalse(self.dict1.is_string)

        self.assertTrue(self.int1.is_number)
        self.assertTrue(self.float1.is_number)
        self.assertFalse(self.string1.is_number)
        self.assertFalse(self.list1.is_number)
        self.assertFalse(self.tuple1.is_number)
        self.assertFalse(self.dict1.is_number)

        self.assertFalse(self.int1.is_array)
        self.assertFalse(self.float1.is_array)
        self.assertFalse(self.string1.is_array)
        self.assertTrue(self.list1.is_array)
        self.assertTrue(self.tuple1.is_array)
        self.assertFalse(self.dict1.is_array)

        self.assertFalse(self.int1.is_object)
        self.assertFalse(self.float1.is_object)
        self.assertFalse(self.string1.is_object)
        self.assertFalse(self.list1.is_object)
        self.assertFalse(self.tuple1.is_object)
        self.assertTrue(self.dict1.is_object)


class TestBinaryFunctions(unittest.TestCase):

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

        context = [('a', '1234'), ('b', r'\d+')]
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
