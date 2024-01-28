"""
    inyoka.utils.macros
    ~~~~~~~~~~~~~~~~~~~

    The module contains the core macros and the logic to find macros.

    The term macro is derived from the MoinMoin wiki engine which refers to
    macros as small pieces of dynamic snippets that are exanded at rendering
    time.  For inyoka macros are pretty much the same just they are always
    expanded at parsing time.  However, for the sake of dynamics macros can
    mark themselves as runtime macros.  In that case during parsing the macro
    is inserted directly into the parsing as as block (or inline, depending on
    the macro settings) node and called once the data is loaded from the
    serialized instructions.

    This leads to the limitation that macros must be pickleable.  So if you
    feel the urge of creating a closure or something similar in your macro
    initializer remember that and move the code into the render method.

    For example macro implementations have a look at this module's sourcecode
    which implements all the builtin macros.


    :copyright: (c) 2007-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime

from django.utils import timezone as dj_timezone
from django.utils.translation import gettext as _

from inyoka.markup import nodes
from inyoka.markup.utils import ArgumentCollector, debug_repr, filter_style
from inyoka.utils.dates import format_datetime

ALL_MACROS = {}


def get_macro(name, args, kwargs):
    """
    Instantiate a new macro or return `None` if it doesn't exist.  This is
    used by the parser when it encounters a `macro_begin` token.  Usually
    there is no need to call this function from outside the parser.  There
    may however be macros that want to extend the functionality of an
    already existing macro.
    """
    cls = ALL_MACROS.get(name)
    if cls is None:
        return
    return cls(args, kwargs)


def register(cls):
    global ALL_MACROS
    names = cls.names
    for name in names:
        if name in ALL_MACROS:
            raise RuntimeError('Macro name "%s" already registered' % name)
        ALL_MACROS[name] = cls


class Macro(metaclass=ArgumentCollector):
    """
    Baseclass for macros.  All macros should extend from that or implement
    the same attributes.  The preferred way however is subclassing.
    """

    #: The canonical names for this macro. A macro may have multiple aliases
    #: e.g to support multiple languages.
    names = ()

    #: if a macro is static this has to be true.
    is_static = False

    #: true if this macro returns a block level node in dynamic
    #: rendering. This does not affect static rendering.
    is_block_tag = False

    #: unused in `Macro` but not `TreeMacro`.
    is_tree_processor = False

    #: set this to True if you want to do the argument parsing yourself.
    has_argument_parser = False

    #: if a macro is dynamic it's unable to emit metadata normally. This
    #: slot allows one to store a list of nodes that are sent to the
    #: stream before the macro itself is emited and removed from the
    #: macro right afterwards so that it consumes less storage pickled.
    metadata = None

    #: the arguments this macro expects
    arguments = ()

    #: The render context this macro is allowed in. Restrictive by default
    allowed_context = None

    __repr__ = debug_repr

    def render(self, context, format):
        """Dispatch to the correct render method."""
        rv = self.build_node(context, format)
        if isinstance(rv, str):
            return rv
        return rv.render(context, format)

    def build_node(self, context=None, format=None):
        """
        If this is a static macro this method has to return a node.  If it's
        a runtime node a context and format parameter is passed.

        A static macro has to return a node, runtime macros can either have
        a look at the passed format and return a string for that format or
        return a normal node which is then rendered into that format.
        """


class TreeMacro(Macro):
    """
    Special macro that is processed after the whole tree was created.  This
    is useful for a `TableOfContents` macro that has to look for headline
    tags etc.

    If a macro is a tree processor the `build_node` function is passed a
    tree as only argument.  That being said it's impossible to use a tree
    macro as runtime macro.
    """

    is_tree_processor = True
    is_static = True

    #: When the macro should be expanded. Possible values are:
    #:
    #: `final`
    #:      the macro is expanded at the end of the transforming process.
    #:
    #: `initial`
    #:      the macro is expanded at the end of the parsing process, before
    #:      the transformers and other tree macro levels (default).
    #:
    #: `late`
    #:      Like initial, but after initial macros.
    stage = 'initial'

    def render(self, context, format):
        """A tree macro is not a runtime macro.  Never static"""
        raise RuntimeError('tree macro is not allowed to be non static')

    def build_node(self, tree):
        """
        Works like a normal `build_node` function but it's passed a node that
        represents the syntax tree.  It can be queried using the query
        interface attached to nodes.

        The return value must be a node, even if the macro shouldn't output
        anything.  In that situation it's recommended to return just an empty
        `nodes.Text`.
        """


class TableOfContents(TreeMacro):
    """
    Show a table of contents.  We do not embedd the TOC in a DIV so far and
    there is also no title on it.
    """

    names = ('TableOfContents', 'Inhaltsverzeichnis')
    stage = 'final'
    is_block_tag = True
    arguments = (
        ('max_depth', int, 3),
        ('type', {
            'unordered': 'unordered',
            'arabic0': 'arabiczero',
            'arabic': 'arabic',
            'alphabeth': 'alphalower',
            'ALPHABETH': 'alphaupper',
            'roman': 'romanlower',
            'ROMAN': 'romanupper'
        }, 'arabic')
    )
    allowed_context = ['ikhaya', 'wiki']

    def __init__(self, depth, list_type):
        self.depth = depth
        self.list_type = list_type

    def build_node(self, tree):
        """Queries for all :class:`nodes.Headline` nodes and constructs a
        :class:`nodes.List` representing the headlines. The optimal result
        will look like::

            = Foo1 =
            == Bar1 ==
            == Bar2 ==
            === Buz1 ===
            = Foo2 =
            == Bar3 ==

            1. Foo1
              1. Bar1
              2. Bar2
                1. Buz1
            2. Foo2
              1. Bar3

        But due to some reasons, there are situations where the headlines
        are not used as one would expect. The level is increased by something
        larger than 1::

            = Foo1 =
            === Buz1 ===
            == Bar1 ==
            === Buz1 ===
            = Foo2 =
            == Bar3 ==

            1. Foo1
                1. Buz1
              2. Bar1
                1. Baz1
            2. Foo2
              1. Bar3
        """

        result = nodes.List(self.list_type)
        stack = [result]
        last_level = 1
        for headline in tree.query.by_type(nodes.Headline):
            # we want to show headlines up to level self.depth; not more
            if headline.level > self.depth:
                continue

            # if the headline is indented compared to the previous one
            # we need to check for the difference between those levels
            # (see second example above)
            if headline.level > last_level:
                for i in range(headline.level - last_level - 1):
                    stack.append(nodes.List(self.list_type))
                    stack[-1].children.append(nodes.ListItem(style='list-style: none'))
                stack.append(nodes.List(self.list_type))
            # we are unindenting the headline level. All lists have to be
            # popped from the stack up to the current level
            elif headline.level < last_level:
                for i in range(last_level - headline.level):
                    n = stack.pop()
                    if stack[-1].children:
                        stack[-1].children[-1].children.append(n)
                    else:
                        stack[-1].children.append(nodes.ListItem([n], style='list-style: none'))

            # in all cases we need to add the current headline to the children
            # of recent stack element
            caption = [nodes.Text(headline.text)]
            link = nodes.Link('#' + headline.id, caption)
            stack[-1].children.append(nodes.ListItem([link]))

            last_level = headline.level

        for i in range(last_level - 1):
            n = stack.pop()
            if stack[-1].children:
                stack[-1].children[-1].children.append(n)
            else:
                stack[-1].children.append(nodes.ListItem([n], style='list-style: none'))
        head = nodes.Layer(children=[nodes.Text(_('Table of contents'))],
                           class_='head')
        result = nodes.Layer(class_='toc toc-depth-%d' % self.depth,
                             children=[head, result])
        return result


class Date(Macro):
    """
    This macro accepts an `iso8601` string or unix timestamp (the latter in
    UTC) and formats it using the `format_datetime` function.
    """
    names = ('Date', 'Datum')
    arguments = (
        ('date', str, None),
    )
    allowed_context = ['ikhaya', 'wiki']

    def __init__(self, date):
        if not date:
            self.now = True
        else:
            self.now = False
            try:
                self.date = datetime.fromisoformat(date)
            except ValueError:
                try:
                    self.date = datetime.utcfromtimestamp(int(date))
                except ValueError:
                    self.date = None

    def build_node(self, context, format):
        if self.now:
            date = dj_timezone.now()
        else:
            date = self.date

        if date is None:
            return nodes.Text(_('Invalid date'))

        return nodes.Text(format_datetime(date))


class Newline(Macro):
    """
    This macro just forces a new line.
    """
    names = ('BR',)
    is_static = True
    allowed_context = ['forum', 'ikhaya', 'wiki']

    def build_node(self):
        return nodes.Newline()


class Anchor(Macro):
    """
    This macro creates an anchor accessible by url.
    """
    names = ('Anchor', 'Anker')
    is_static = True
    arguments = (
        ('id', str, None),
    )
    allowed_context = ['forum', 'ikhaya', 'wiki']

    def __init__(self, id):
        self.id = id

    def build_node(self):
        return nodes.Link('#%s' % self.id, id=self.id, class_='anchor',
                          children=[nodes.Text('⚓︎')])


class Span(Macro):
    names = ('SPAN',)
    is_static = True
    arguments = (
        ('content', str, ''),
        ('class_', str, None),
        ('style', str, None),
    )
    allowed_context = ['forum', 'ikhaya', 'wiki']

    def __init__(self, content, class_, style):
        self.content = content
        self.class_ = class_
        self.style = filter_style(style) or None

    def build_node(self):
        return nodes.Span(children=[nodes.Text(self.content)],
                        class_=self.class_, style=self.style)


register(Anchor)
register(Newline)
register(Date)
register(TableOfContents)
register(Span)
