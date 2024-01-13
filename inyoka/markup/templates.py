r"""
    inyoka.markup.templates
    ~~~~~~~~~~~~~~~~~~~~~~~

    This module implements the templating language for the Wiki.  It's a
    very simple language with some syntax elements taken from both Python
    and PHP.

    The following syntax elements exist::

        <@ for $author in $authors @>
          * <@ $author @>
        <@ endfor @>

        <@ if $author == current_page @>
          * '''$author'''
        <@ else @>
          * [:$author:]
        <@ endif @>

    The start tags (``<@``) delete one leading newline.


    :copyright: (c) 2007-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import re
import random
import operator
from functools import total_ordering, partial

from django.utils.encoding import smart_str
from django.utils.translation import gettext as _

from inyoka.markup.base import escape, unescape_string
from inyoka.markup.parsertools import TokenStream
from inyoka.markup.utils import debug_repr, has_key, join_array, regex_match, simple_match
from inyoka.wiki.exceptions import CaseSensitiveException


def process(source, context=()):
    """Parse and evaluate a template."""
    return Parser(source).parse().to_markup(Context(context))


def expand_page_template(template, context, macro_behavior=False):
    """A helper for the template macro and wiki-parser."""
    from inyoka.wiki.models import Page
    from inyoka.markup import nodes
    if template is None:
        if not macro_behavior:
            raise ValueError('no template given')
        return nodes.error_box(_('Invalid arguments'),
                               _('The first argument must be the name of the template.'))
    try:
        page = Page.objects.get_by_name(template, raise_on_deleted=True)
    except Page.DoesNotExist:
        if not macro_behavior:
            raise
        return nodes.error_box(_('Missing template'),
                               _('The template “%(name)s” could not be found.')
                               % {'name': template})
    except CaseSensitiveException as e:
        page = e.page
    doc = page.rev.text.parse(context)
    children, is_block_tag = doc.get_fragment_nodes(True)

    # children is a reference to a list in a node.  We don't want to
    # alter that here as a side effect so we create a copy.
    if macro_behavior:
        children = children + [nodes.MetaData('X-Attach', (template,))]
    return nodes.Container(children)


def ruleset(*args):
    return args


def rule(regexp, tokentype=None, enter=None, leave=None):
    statechange = enter or leave
    return (re.compile(regexp, re.U), tokentype, statechange)


number_re = re.compile(r'^\d+(?:\.\d*)?$')


class Lexer:
    """
    Tokenize template code.
    """
    rules = {
        'root': ruleset(
            rule(r'\n?<@', 'tag_begin', enter='tag'),
            rule(r'^##.*?(\n|$)(m)')
        ),
        'tag': ruleset(
            rule(r'@>', 'tag_end', leave=1),
            rule(r'(?m)#.*?$'),
            rule(r'\s+'),
            rule(r'\d+(\.\d*)?', 'number'),
            rule(r"(?s)('([^'\\]*(?:\\.[^'\\]*)*)'|"
                 r'"([^"\\]*(?:\\.[^"\\]*)*)")', 'string'),
            rule(r'(<=?|>=?|=>|[!=]?=)|[()\[\]&.,*%/+-]', 'operator'),
            rule(r'\$[^\W\d][^\W]*', 'variable')
        )
    }

    def tokenize(self, code):
        return TokenStream.from_tuple_iter(self._tokenize(code))

    def _tokenize(self, code):
        code = '\n'.join(smart_str(obj) for obj in code.splitlines())
        pos = 0
        end = len(code)
        stack = ['root']
        text_buffer = []
        flatten = ''.join
        add_text = text_buffer.append

        while pos < end:
            for regexp, tokentype, statechange in self.rules[stack[-1]]:
                m = regexp.match(code, pos)
                if m is None:
                    continue
                if text_buffer:
                    yield 'raw', flatten(text_buffer)
                    del text_buffer[:]
                if tokentype is not None:
                    yield tokentype, m.group()
                pos = m.end()
                if statechange is not None:
                    if isinstance(statechange, int):
                        del stack[-statechange:]
                    else:
                        stack.append(statechange)
                break
            else:
                add_text(code[pos])
                pos += 1

        if text_buffer:
            yield 'raw', flatten(text_buffer)


class Parser:
    """
    Parse template code.
    """

    def __init__(self, code):
        self.stream = Lexer().tokenize(code)
        self.handlers = {
            'for': self.parse_for,
            'if': self.parse_if
        }

    def parse_for(self):
        next(self.stream)
        if not self.stream.test('variable'):
            raise TemplateSyntaxError(
                _('Invalid syntax for this loop. The first argument '
                  'must be a variable.'))
        variable = self.stream.current.value[1:]
        next(self.stream)
        if not self.stream.test('raw', 'in'):
            raise TemplateSyntaxError(
                _('Invalid syntax for this loop. After the first variable '
                  'an “in” is required.'))
        next(self.stream)
        seq = self.parse_expr()
        if not self.stream.test('tag_end'):
            raise TemplateSyntaxError(_('Loop header contains too many arguments.'))
        next(self.stream)
        body = self.subparse(lambda: self.stream.test('raw', 'endfor'))
        if not self.stream.test('tag_end'):
            raise TemplateSyntaxError(_('Loop end contains too many arguments.'))
        next(self.stream)
        return For(variable, seq, body)

    def parse_if(self):
        next(self.stream)
        expr = self.parse_expr()
        if not self.stream.test('tag_end'):
            raise TemplateSyntaxError(
                _('Conditions allow only one expression per block.'))
        next(self.stream)
        tests = [(expr, self.subparse(lambda: self.stream.test('raw',
                 ('endif', 'else', 'elseif')), drop_needle=False))]
        else_body = None

        while True:
            if self.stream.test('raw', 'else'):
                next(self.stream)
                if not self.stream.test('tag_end'):
                    raise TemplateSyntaxError(
                        _('The “else” block does not allow any expressions. '
                          'Maybe you wanted to use the “elseif” block.'))
                next(self.stream)
                else_body = self.subparse(lambda:
                                           self.stream.test('raw', 'endif'),
                                           drop_needle=False)
            elif self.stream.test('raw', 'elseif'):
                next(self.stream)
                expr = self.parse_expr()
                if not self.stream.test('tag_end'):
                    raise TemplateSyntaxError(
                        _('Conditions allow only one expression per block.'))
                next(self.stream)
                tests.append((expr, self.subparse(lambda:
                             self.stream.test('raw', ('endif', 'elseif', 'else')),
                             drop_needle=False)))
                continue
            break
        next(self.stream)
        if not self.stream.test('tag_end'):
            raise TemplateSyntaxError(_('“endif” does not allow any arguments'))
        next(self.stream)
        return If(tests, else_body)

    def parse_expr(self):
        return self.parse_or()

    def parse_or(self):
        left = self.parse_and()
        while self.stream.test('raw', 'or'):
            next(self.stream)
            left = Or(left, self.parse_and())
        return left

    def parse_and(self):
        left = self.parse_binary_function()
        while self.stream.test('raw', 'and'):
            next(self.stream)
            left = And(left, self.parse_binary_function())
        return left

    def parse_binary_function(self):
        left = self.parse_convert()
        functions = tuple(BINARY_FUNCTIONS)
        while self.stream.test('raw', functions):
            func = BINARY_FUNCTIONS[self.stream.current.value]
            next(self.stream)
            left = BinaryFunction(left, self.parse_convert(), func)
        return left

    def parse_convert(self):
        left = self.parse_test()
        if self.stream.test('raw', 'as'):
            next(self.stream)
            if not self.stream.test('raw', tuple(CONVERTER)):
                raise TemplateSyntaxError(
                    _('Unknown expression after “as” operator.'))
            func = CONVERTER[self.stream.current.value]
            next(self.stream)
            left = ConverterFunction(left, func)
        return left

    def parse_test(self):
        left = self.parse_cmp()
        if self.stream.test('raw', 'is'):
            next(self.stream)
            if self.stream.test('raw', 'not'):
                negated = True
                next(self.stream)
            else:
                negated = False
            if not self.stream.test('raw', tuple(TESTS)):
                raise TemplateSyntaxError(
                    _('Unknown expression after “is” operator'))
            func = TESTS[self.stream.current.value]
            next(self.stream)
            left = TestFunction(left, func, negated)
        return left

    def parse_cmp(self):
        known_operators = {
            '==': 'eq',
            '!=': 'ne',
            '>': 'gt',
            '>=': 'ge',
            '<': 'lt',
            '<=': 'le'
        }
        left = self.parse_add()
        while not self.stream.eof:
            if self.stream.current.type == 'operator' and \
               self.stream.current.value in known_operators:
                op = known_operators[self.stream.current.value]
                next(self.stream)
                left = Cmp(op, left, self.parse_add())
            else:
                break
        return left

    def parse_add(self):
        left = self.parse_sub()
        while self.stream.test('operator', '+'):
            next(self.stream)
            left = Add(left, self.parse_sub())
        return left

    def parse_sub(self):
        left = self.parse_concat()
        while self.stream.test('operator', '-'):
            next(self.stream)
            left = Sub(left, self.parse_concat())
        return left

    def parse_concat(self):
        left = self.parse_mul()
        while self.stream.test('operator', '&'):
            next(self.stream)
            left = Concat(left, self.parse_mul())
        return left

    def parse_mul(self):
        left = self.parse_div()
        while self.stream.test('operator', '*'):
            next(self.stream)
            left = Mul(left, self.parse_div())
        return left

    def parse_div(self):
        left = self.parse_mod()
        while self.stream.test('operator', '/'):
            next(self.stream)
            left = Div(left, self.parse_mod())
        return left

    def parse_mod(self):
        left = self.parse_neg()
        while self.stream.test('operator', '%'):
            next(self.stream)
            left = Mod(left, self.parse_neg())
        return left

    def parse_neg(self):
        if self.stream.test('operator', '-'):
            next(self.stream)
            return Neg(self.parse_primary())
        return self.parse_primary()

    def parse_primary(self):
        token_type, value = self.stream.current
        next(self.stream)
        if token_type == 'eof':
            node = TemplateSyntaxError(_('Unexpected end of expression.'))
        elif token_type == 'number':
            node = Value(float(value))
        elif token_type == 'variable':
            node = Var(value[1:])
        elif token_type == 'string':
            node = Value(unescape_string(value[1:-1]))
        elif token_type == 'operator':
            if value == '(':
                node = self.parse_expr()
                if not self.stream.test('operator', ')'):
                    raise TemplateSyntaxError(
                        _('Parentheses were not closed properly.'))
            elif value == '[':
                keys = []
                values = []
                next_numeric = 0
                is_list = True
                while self.stream.current.value != ']':
                    if values:
                        if not self.stream.test('operator', ','):
                            raise TemplateSyntaxError(
                                _('Missing comma between array entries'))
                        next(self.stream)
                    value = self.parse_expr()
                    if self.stream.test('operator', '=>'):
                        is_list = False
                        next(self.stream)
                        key = value
                        value = self.parse_expr()
                        # that's ridiculous but PHP behavior and we should
                        # stick to that as it's very beginner friendly.
                        as_int = int(value)
                        if as_int > next_numeric and as_int == float(value):
                            next_numeric = as_int + 1
                    else:
                        key = Value(next_numeric)
                        next_numeric += 1
                    keys.append(key)
                    values.append(value)
                if is_list:
                    node = Value(values)
                else:
                    node = Value(dict(list(zip(keys, values))))
            else:
                raise TemplateSyntaxError(_('Unexpected operator'))
            next(self.stream)
        else:
            node = Value(value)
        return self.parse_postfix(node)

    def parse_postfix(self, node):
        while True:
            if self.stream.test('operator', '.'):
                node = self.parse_getitem(node)
            else:
                break
        return node

    def parse_getitem(self, node):
        next(self.stream)
        if self.stream.test('variable'):
            item = Var(self.stream.current.value[1:])
            next(self.stream)
        elif self.stream.test('raw'):
            item = Value(self.stream.current.value)
            next(self.stream)
        elif self.stream.test('number'):
            item = Value(float(self.stream.current.value))
            next(self.stream)
        else:
            raise TemplateSyntaxError(
                _('expected variable, integer or attribute'))
        return GetItem(node, item)

    def subparse(self, test, drop_needle=True):
        result = []
        next_token = partial(next, self.stream)

        def assemble_compound():
            if len(result) == 1:
                return result[0]
            return Compound(result)

        try:
            while not self.stream.eof:
                token_type = self.stream.current.type
                if token_type == 'tag_begin':
                    next_token()
                    if test is not None and test():
                        if drop_needle:
                            next_token()
                        return assemble_compound()
                    if self.stream.current.type == 'raw':
                        handler = self.handlers.get(self.stream.current.value)
                        if handler is not None:
                            node = handler()
                            if node is not None:
                                result.append(node)
                            continue
                    result.append(self.parse_expr())
                    if not self.stream.test('tag_end'):
                        raise TemplateSyntaxError(
                            _('Too many arguments for this value output'))
                    next_token(self.stream)
                elif token_type == 'raw':
                    result.append(Data(self.stream.current.value))
                    next_token()
                else:
                    assert 0, 'arrrr. the lexer screwed us'
        except TemplateSyntaxError as exc:
            result.append(exc.get_node())
        return assemble_compound()

    def parse(self):
        return Template(self.subparse(None))


class TemplateSyntaxError(Exception):
    """
    Helper for the parser.  Translates into a node in the parsing process.
    """

    def __init__(self, message):
        self.message = message
        Exception.__init__(self, message)

    def get_node(self):
        msg = _('Invalid syntax: ')
        return Data("\n\n'''%s''' %s\n\n" % (msg, self.message))


class Context:
    """
    Creates a context of values out of a list of tuples in the form
    ``(key, value)``.

    Example::

        [('foo.0', 1),
         ('foo.1', 2),
         ('foo.2.a', 1),
         ('foo.2.b', 2),
         ('bar', 23),
         ('baz', "blub")]

    Converts internally to::

        {'foo': Value([1, 2, Value({'a': Value(1), 'b': Value(2)})]),
         'bar': Value(23),
         'baz': Value("blub")}
    """

    def __init__(self, items=()):
        def to_array(items):
            d = dict(items)
            l = [NoneValue] * len(d)
            try:
                for k, v in d.items():
                    l[k] = v
            except (IndexError, ValueError, TypeError):
                return Value(d)
            return Value(l)

        def to_dict(items):
            open = {}
            result = []
            for parts, value in items:
                key = parts[0]
                if key.isdigit():
                    key = int(key)
                if len(parts) > 1:
                    open.setdefault(key, []).append((parts[1:], value))
                    result.append((key, None))
                else:
                    result.append((key, Value(value)))
            if open:
                for idx, (key, value) in enumerate(result):
                    if value is None:
                        result[idx] = (key, to_array(to_dict(open[key])))
            return dict(result)
        self.stack = [to_dict((x.split('.'), y) for x, y in items), {}]

    def push(self):
        self.stack.append({})

    def pop(self):
        self.stack.pop()

    def __getitem__(self, key):
        for storage in reversed(self.stack):
            try:
                return storage[int(key)]
            except (ValueError, TypeError, KeyError):
                try:
                    return storage[str(key)]
                except KeyError:
                    pass
        return NoneValue

    def __setitem__(self, key, value):
        self.stack[-1][key] = value


class Node:

    __repr__ = debug_repr

    def to_markup(self, context):
        return ''.join(self.stream_markup(context))

    def stream_markup(self, context):
        pass


class Compound(Node):

    def __init__(self, nodes):
        self.nodes = nodes

    def stream_markup(self, context):
        for node in self.nodes:
            yield from node.stream_markup(context)


class Template(Node):

    def __init__(self, body):
        self.body = body

    def stream_markup(self, context):
        yield from self.body.stream_markup(context)


class Data(Node):

    def __init__(self, markup):
        self.markup = markup

    def stream_markup(self, context):
        yield self.markup


class For(Node):

    def __init__(self, var, seq, body):
        self.var = var
        self.seq = seq
        self.body = body

    def stream_markup(self, context):
        context.push()
        seq = self.seq.evaluate(context)
        length = len(seq)
        for idx, child in enumerate(seq):
            context[self.var] = Value(child)
            context['loop'] = Value({
                'index0': idx,
                'index': idx + 1,
                'revindex0': length - idx - 1,
                'revindex': length - idx,
                'length': length,
                'first': idx == 0,
                'last': idx == length - 1
            })
            yield from self.body.stream_markup(context)
        context.pop()


class If(Node):

    def __init__(self, tests, else_body):
        self.tests = tests
        self.else_body = else_body

    def stream_markup(self, context):
        for test, body in self.tests:
            if test.evaluate(context):
                yield from body.stream_markup(context)
                break
        else:
            if self.else_body:
                yield from self.else_body.stream_markup(context)


class Expr(Node):

    def evaluate(self, context):
        return NoneValue

    def stream_markup(self, context):
        yield str(self.evaluate(context))


@total_ordering
class Value(Expr):

    def __init__(self, value):
        self.value = value

    def evaluate(self, context):
        return self

    def __bool__(self):
        if self.value in ('0', '0.0'):
            return False
        return bool(self.value)

    def __float__(self, default=0.0):
        this = self.value
        if isinstance(this, (int, float)):
            return float(this)
        elif isinstance(this, str):
            m = number_re.search(this.strip())
            if m:
                return float(m.group())
        return default

    def __int__(self):
        return int(self.__float__(0))

    def __iter__(self):
        if isinstance(self.value, (tuple, list, str)):
            yield from self.value
        elif isinstance(self.value, dict):
            for key, value in self.value.items():
                yield {'key': key, 'value': value}

    def __len__(self):
        if isinstance(self.value, (list, tuple, dict, str)):
            return len(self.value)
        return 0

    def __getitem__(self, key):
        try:
            return self.value[int(key)]
        except (ValueError, TypeError, IndexError, KeyError):
            try:
                return self.value[str(key)]
            except (KeyError, TypeError):
                pass
        return NoneValue

    def __str__(self):
        if self.value is None:
            return ''
        elif self.value in (True, False):
            return self.value and '1' or '0'
        elif isinstance(self.value, (tuple, list)):
            return ', '.join(str(x) for x in self.value)
        elif isinstance(self.value, dict):
            return ', '.join('%s: %s' % x for x in self.value.items())
        return str(self.value)

    def __hash__(self):
        if isinstance(self.value, (list, tuple)):
            return hash(tuple(self.value))
        elif isinstance(self.value, dict):
            return hash(tuple(self.value.items()))
        return hash(str(self))

    def __eq__(self, other):
        if isinstance(self.value, (list, tuple, dict)):
            return self.value == other.value
        if str(self) == str(other):
            return True
        missing = object()
        a = self.__float__(missing)
        if isinstance(other, Value):
            b = other.__float__(missing)
        else:
            try:
                b = float(other)
            except (ValueError, TypeError):
                return False
        if a is missing or b is missing:
            return False
        return a == b

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        return float(self) < float(other)

    def __add__(self, other):
        if isinstance(self.value, (tuple, list)) and \
           isinstance(other.value, (tuple, list)):
            result = []
            result.extend(self.value)
            result.extend(other.value)
            return Value(result)
        if isinstance(self.value, dict) and \
             isinstance(other.value, dict):
            result = {}
            result.update(self.value)
            result.update(other.value)
            return Value(result)
        if isinstance(self.value, (int, float, str)) and \
           isinstance(other.value, (int, float, str)):
            return Value(self.value + other.value)
        return Value(None)

    def __sub__(self, other):
        if isinstance(self.value, (int, float)) and \
           isinstance(other.value, (int, float)):
            return Value(self.value - other.value)
        return Value(None)

    def __mul__(self, other):
        if isinstance(self.value, (int, float)) and \
           isinstance(other.value, (int, float)):
            return Value(self.value * other.value)
        return Value(None)

    def __truediv__(self, other):
        try:
            if isinstance(self.value, (int, float)) and \
               isinstance(other.value, (int, float)):
                return Value(self.value / other.value)
            return Value(None)
        except ZeroDivisionError:
            return NaN

    def __mod__(self, other):
        try:
            if isinstance(self.value, (int, float)) and \
               isinstance(other.value, (int, float)):
                return Value(self.value % other.value)
            return Value(None)
        except ZeroDivisionError:
            return NaN

    def __and__(self, other):
        return Value(str(self) + str(other))

    def __contains__(self, obj):
        if isinstance(self.value, (tuple, list, dict)):
            return obj in self.value
        return str(obj) in str(self)

    @property
    def is_string(self):
        return isinstance(self.value, str)

    @property
    def is_number(self):
        return isinstance(self.value, (int, float))

    @property
    def is_array(self):
        return isinstance(self.value, (tuple, list))

    @property
    def is_object(self):
        return isinstance(self.value, dict)

    def __repr__(self):
        return '%s(%r)' % (
            self.__class__.__name__,
            self.value
        )


NoneValue = Value(None)
_inf = float('1e1000000')
NaN = Value(_inf / _inf)
del _inf


class Var(Expr):

    def __init__(self, name):
        self.name = name

    def evaluate(self, context):
        return context[self.name]


class Bin(Expr):
    operation = None

    def __init__(self, left, right):
        self.left = left
        self.right = right

    def evaluate(self, context):
        return self.operation(
            self.left.evaluate(context),
            self.right.evaluate(context)
        )


class And(Bin):

    def evaluate(self, context):
        val = self.left.evaluate(context)
        if not val:
            return val
        return self.right.evaluate(context)


class Or(Bin):

    def evaluate(self, context):
        val = self.left.evaluate(context)
        if val:
            return val
        return self.right.evaluate(context)


class Add(Bin):
    operation = operator.add


class Sub(Bin):
    operation = operator.sub


class Mul(Bin):
    operation = operator.mul


class Div(Bin):
    operation = operator.truediv


class Mod(Bin):
    operation = operator.mod


class Concat(Bin):
    operation = operator.and_


class Cmp(Bin):

    def __init__(self, op, left, right):
        self.operation = getattr(operator, op)
        Bin.__init__(self, left, right)


class Neg(Expr):

    def __init__(self, expr):
        self.expr = expr

    def evaluate(self, context):
        return -self.expr.evaluate(context)


class GetItem(Expr):

    def __init__(self, expr, item):
        self.expr = expr
        self.item = item

    def evaluate(self, context):
        return self.expr.evaluate(context)[self.item.evaluate(context)]


class BinaryFunction(Expr):

    def __init__(self, left, right, func):
        self.left = left
        self.right = right
        self.func = func

    def evaluate(self, context):
        return Value(self.func(self.left.evaluate(context),
                               self.right.evaluate(context)))


class ConverterFunction(Expr):

    def __init__(self, expr, func):
        self.expr = expr
        self.func = func

    def evaluate(self, context):
        return Value(self.func(self.expr.evaluate(context)))


class TestFunction(Expr):

    def __init__(self, expr, func, negated):
        self.expr = expr
        self.func = func
        self.negated = negated

    def evaluate(self, context):
        rv = self.func(self.expr.evaluate(context))
        if self.negated:
            return Value(not rv)
        return Value(bool(rv))


BINARY_FUNCTIONS = {
    'contain': lambda a, b: b in a,
    'contains': lambda a, b: b in a,
    'has_key': has_key,
    'starts_with': lambda a, b: str(a).startswith(str(b)),
    'ends_with': lambda a, b: str(a).endswith(str(b)),
    'matches': lambda a, b: simple_match(str(b), str(a)),
    'matches_regex': lambda a, b: regex_match(str(b), str(a)),
    'join_with': join_array,
    'split_by': lambda a, b: str(a).split(str(b)),
}

CONVERTER = {
    'string': lambda x: str(x),
    'number': lambda x: float(x),
    'int': lambda x: int(x),
    'uppercase': lambda x: str(x).upper(),
    'lowercase': lambda x: str(x).lower(),
    'title': lambda x: str(x).title(),
    'stripped': lambda x: str(x).strip(),
    'rounded': lambda x: round(float(x)),
    'quoted': lambda x: "%s" % str(x) .
    replace('\\', '\\\\') .
    replace('"', '\\"'),
    'escaped': lambda x: escape(str(x)),
    'array_of_lines': lambda x: str(x).splitlines(),
    'randint': lambda x: float(random.randint(1.0, x))
}

TESTS = {
    'even': lambda x: int(x) % 2 == 0,
    'odd': lambda x: int(x) % 2 != 0,
    'uppercase': lambda x: str(x).isupper(),
    'lowercase': lambda x: str(x).islower(),
    'string': lambda x: x.is_string,
    'number': lambda x: x.is_number,
    'array': lambda x: x.is_array,
    'object': lambda x: x.is_object,
    'defined': lambda x: x.value is not None,
    'undefined': lambda x: x.value is None
}
