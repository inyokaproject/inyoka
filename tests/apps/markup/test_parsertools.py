"""
tests.apps.markup.test_parsertools
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test inyoka's markup parsertools.

:copyright: (c) 2007-2026 by the Inyoka Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

import io
import unittest

from inyoka.markup.parsertools import (
    MultiMap,
    Token,
    TokenStream,
    TokenStreamIterator,
    _unpickle_multimap,
    flatten_iterator,
)


class ParserToolsTestCase(unittest.TestCase):
    def test_token_stream_iterator(self):
        stream = TokenStream(iter([Token('text', 'a'), Token('text', 'b')]))
        iterator = TokenStreamIterator(stream)

        self.assertIs(iterator.__iter__(), iterator)
        self.assertEqual(next(iterator), Token('text', 'a'))
        self.assertEqual(next(iterator), Token('text', 'b'))
        with self.assertRaises(StopIteration):
            next(iterator)

    def test_token_stream_initialization_and_eof(self):
        stream = TokenStream(iter([]))
        self.assertTrue(stream.eof)
        self.assertEqual(stream.current.type, 'eof')

        stream = TokenStream.from_tuple_iter([('text', 'a'), ('text', 'b')])
        self.assertEqual(stream.current, Token('text', 'a'))

        self.assertEqual(list(stream), [Token('text', 'a'), Token('text', 'b')])

    def test_token_stream_debug_look_push(self):
        stream = TokenStream(iter([Token('first', 1), Token('second', 2)]))

        self.assertEqual(stream.look(), Token('second', 2))
        self.assertEqual(stream.current, Token('first', 1))

        stream.push(Token('queued', 'x'))
        self.assertEqual(stream.look(), Token('queued', 'x'))
        self.assertEqual(stream.current, Token('first', 1))

    def test_token_stream_skip(self):
        stream = TokenStream(iter([Token('first', 1), Token('second', 2)]))
        stream.skip(1)
        self.assertEqual(stream.current, Token('second', 2))

    def test_token_stream_push(self):
        stream = TokenStream(iter([Token('first', 1), Token('second', 2)]))
        stream.push(Token('queued', 'x'), current=True)
        self.assertEqual(stream.current, Token('queued', 'x'))
        self.assertEqual(stream.look(), Token('second', 2))

    def test_token_stream_debug(self):
        stream = TokenStream(iter([Token('word', 'value'), Token('other', 'x')]))
        output = io.StringIO()
        stream.debug(output)

        self.assertIn("Token(type='word', value='value')", output.getvalue())

    def test_token_stream_test(self):
        stream = TokenStream(iter([Token('word', 'value'), Token('other', 'x')]))

        self.assertTrue(stream.test('word'))
        self.assertTrue(stream.test('word', 'value'))
        self.assertFalse(stream.test('word', 'other'))

    def test_token_stream_expect(self):
        stream = TokenStream(iter([Token('word', 'value'), Token('other', 'x')]))

        self.assertEqual(stream.expect('word', 'value'), Token('word', 'value'))
        self.assertEqual(stream.current, Token('other', 'x'))
        self.assertEqual(stream.expect('other', 'x'), Token('other', 'x'))
        self.assertTrue(stream.eof)

    def test_token_stream_shift(self):
        stream = TokenStream(iter([Token('current', 'now')]))
        stream.shift(Token('inserted', 'value'))

        self.assertEqual(stream.current, Token('inserted', 'value'))
        self.assertEqual(stream.look(), Token('current', 'now'))

    def test_multimap(self):
        data = MultiMap([('a', 1), ('a', 2), ('b', 3)])

        self.assertEqual(data['a'], [1, 2])
        self.assertEqual(data['missing'], [])
        self.assertEqual(data.get('a'), 1)
        self.assertIsNone(data.get('missing'))

        with self.assertRaises(TypeError):
            data['new'] = 4
        with self.assertRaises(TypeError):
            data.setdefault('new', 4)
        with self.assertRaises(TypeError):
            data.update({'new': 4})
        with self.assertRaises(TypeError):
            del data['a']

        self.assertEqual(dict(data), {'a': [1, 2], 'b': [3]})
        self.assertEqual(
            data.__reduce__(), (_unpickle_multimap, ({'a': [1, 2], 'b': [3]},))
        )
        self.assertEqual(
            repr(data),
            "MultiMap([('a', 1), ('a', 2), ('b', 3)])",
        )
        self.assertEqual(_unpickle_multimap(dict(data))['a'], [1, 2])

    def test_flatten_iterator(self):
        source = [1, [2, (3, 4)], 'keep', [[5], 6], None, [7]]
        self.assertEqual(
            list(flatten_iterator(source)),
            [1, 2, 3, 4, 'keep', 5, 6, None, 7],
        )
