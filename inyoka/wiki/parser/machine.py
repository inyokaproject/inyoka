# -*- coding: utf-8 -*-
"""
    inyoka.wiki.parser.machine
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    This implements the ast compiler and evaluator.  Most of the functionality
    here is available on the nodes itself because they mix those classes in,
    the renderer for compiled instructions is importable from the normal
    parser package.

    :copyright: (c) 2007-2012 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import re
from cPickle import loads, dumps, HIGHEST_PROTOCOL
from inyoka.wiki.parser.lexer import escape
from inyoka.utils import get_request_context


_whitespace_re = re.compile('\s+')


class NodeCompiler(object):
    """
    MixIn class for node instruction compiling.  Most nodes mix this class in
    and obtain the `compile` method because of that.
    """

    def compile(self, format):
        """Return a compiled instruction set."""
        assert not '\0' in format
        result = []
        text_buffer = []
        is_dynamic = False

        for item in self.prepare(format):
            if isinstance(item, basestring):
                text_buffer.append(item)
            else:
                if text_buffer:
                    result.append(u''.join(text_buffer))
                    del text_buffer[:]
                result.append(item)
                is_dynamic = True
        if text_buffer:
            result.append(u''.join(text_buffer))

        if not is_dynamic:
            return '!%s\0%s' % (format, u''.join(result).encode('utf-8'))
        return '@' + dumps((format, result), HIGHEST_PROTOCOL)


class NodeRenderer(object):
    """
    MixedIn on all nodes so that you can render a node without compiling.

    Nodes as such do not know how to render their own structure.  That's up
    to the `Renderer` which uses the instructions from either a node passed
    or a compiled instruction set.  However this class is implemented by all
    non basic nodes and allows to `stream` and `render` the generated markup
    without having to instanciate a `Renderer`.
    """

    def stream(self, context, format):
        """Constructs a renderer for this node and streams it."""
        return Renderer(self).stream(context, format)

    def render(self, context, format):
        """Constructs a renderer for this nodes and renders it."""
        return Renderer(self).render(context, format)

    def to_markup(self, writer=None):
        """Convert the node to markup."""
        if writer is None:
            writer = MarkupWriter()
        self.generate_markup(writer)
        return writer.finish().strip('\n').strip('\\\\')


class NodeQueryInterface(object):
    """
    Adds a `query` property to nodes implementing this interface.  The query
    attribute returns a new `Query` object for the node that implements the
    query interface.
    """

    @property
    def query(self):
        return Query((self,))


class Query(object):
    """
    Helper class to traverse a tree of nodes.  Useful for tree processor
    macros that collect data from the final tree.
    """

    def __init__(self, nodes, recurse=True):
        self.nodes = nodes
        self._nodeiter = iter(self.nodes)
        self.recurse = recurse

    def __iter__(self):
        return self

    def next(self):
        return self._nodeiter.next()

    @property
    def has_any(self):
        """Return `True` if at least one node was found."""
        try:
            self._nodeiter.next()
        except StopIteration:
            return False
        return True

    @property
    def children(self):
        """Return a new `Query` just for the direct children."""
        return Query(self.nodes, False)

    @property
    def all(self):
        """Retrun a `Query` object for all nodes this node holds."""
        def walk(nodes):
            for node in nodes:
                yield node
                if self.recurse and node.is_container:
                    for result in walk(node.children):
                        yield result
        return Query(walk(self))

    def by_type(self, type):
        """Performs an instance test on all nodes."""
        return Query(n for n in self.all if isinstance(n, type))

    def text_nodes(self):
        """Only text nodes."""
        return Query(n for n in self.all if n.is_text_node)


class RenderContext(object):
    """
    Holds information for the rendering systems.  This can be used by macros
    to get a reference to the current context object, the wiki page that
    triggered the rendering or if the rendering should happen in simplified
    mode (disables dynamic macros).

    Per definition a render context must be recreated before a rendering but
    shared among subrenderings.  For example if you include a page you have
    to pass the render context object around.  The reason for this is that
    only that allows you to track circular page inclusions.
    """

    def __init__(self, request=None, wiki_page=None, simplified=False,
                 raw=False, application=None, forum_post=None):
        self.request = request
        self.wiki_page = wiki_page
        self.forum_post = forum_post
        self.simplified = simplified
        self.included_pages = set()
        self._application = application

    @property
    def application(self):
        if self._application is not None:
            return self._application
        return get_request_context(self.request)



class Renderer(object):
    """
    This class can render nodes and compiled structures.  One can pass it a
    node or a compiler instruction set (compiled by a `NodeCompiler`).  In
    the first case the render method expects a `format` argument, in the
    latter the format argument should be ommited or must match the format of
    the compiled instruction set.

    Instead of instanciating this class with a node it's a better idea to use
    the `NodeRenderer` interface implemented by all concrete nodes.
    """

    def __init__(self, obj):
        if isinstance(obj, str):
            self.node, self.format, self.instructions = None, None, None
            if obj[0] == '!':
                pos = obj.index('\0')
                self.format = obj[1:pos]
                self.instructions = [obj[pos + 1:].decode('utf-8')]
            elif obj[0] == '@':
                self.format, self.instructions = loads(obj[1:])
        else:
            self.instructions = None
            self.node = obj
            self.format = None

    def stream(self, context, format=None):
        """
        Creates a generator that yields the results of the instructions
        attached to the renderer.  If the renderer was constructed from
        an instruction set you should not provide format so that it can
        use the format of the instruction set.  If you do provide it the
        two format definitions must match.

        If a node is attached to the renderer it will be prepared on the
        fly but the format parameter is mandatory then.
        """
        if (self.format is not None and format is not None) \
           and self.format != format:
            raise TypeError('this renderer was contructed from an '
                            'compiled instruction set for %r and cannot '
                            'render %r.' % (self.format, format))
        elif self.instructions is None:
            if format is None:
                raise TypeError('You have to provide a format if you '
                                'want to render a node without compiling.')
            instructions = self.node.prepare(format)
        else:
            instructions = self.instructions
        format = format or self.format

        for instruction in instructions:
            if isinstance(instruction, basestring):
                yield instruction
            # if we are in simplified rendering mode dynamic macros
            # and other funny things are not supported. so we fail
            # silently.
            elif not context.simplified:
                yield instruction.render(context, format)

    def render(self, context, format=None):
        """Streams into a buffer and returns it as string."""
        return u''.join(self.stream(context, format))


class MarkupWriter(object):
    """
    Helper function to generate Markup.  It's used to generate wiki markup
    from nodes.  Note that not all nodes have markup associated.
    """

    def __init__(self):
        self._result = []
        self._indentation = []
        self._blocks = []
        self._lists = []
        self._newline = False
        self._new_paragraph = False
        self._new_break = False
        self._escapes = []

    @property
    def is_oneline(self):
        return self._blocks and self._blocks[-1] == 'oneline' \
               and not self.is_raw

    @property
    def is_raw(self):
        return self._indentation and self._indentation[-1][0] == 'raw'

    def touch_whitespace(self):
        self.text(' ')

    def finish(self):
        return u''.join(self._result)

    def flush(self):
        def _indent():
            indentation = []
            for t, depth in self._indentation:
                if t == 'raw':
                    del indentation[:]
                elif t == 'quote':
                    if indentation and indentation[-1] == '> ':
                        indentation[-1:] = ('>', '> ')
                    else:
                        indentation.append('> ')
                elif t == 'indent':
                    indentation.append(u' ' * depth)
            self._result.append(u''.join(indentation))

        if self._newline or self._new_paragraph or self._new_break:
            if self._new_break:
                self._result.append(u'\\\\\n')
                _indent()
            elif self._new_paragraph:
                self._result.append(u'\n')
                _indent()
                self._result.append(u'\n')
                _indent()
            elif self._newline:
                self._result.append(u'\n')
                _indent()
            self._newline = self._new_paragraph = self._new_break = False

    def escape_text(self, text):
        return escape(text)

    def text(self, text):
        self.flush()
        for s in self._escapes:
            text = text.replace(s, u'\\%s' % s)
        if not self.is_raw:
            text = self.escape_text(text)
            text = _whitespace_re.sub(u' ', text)
        self._result.append(text)

    def markup(self, text):
        self.flush()
        self._result.append(text)

    def newline(self):
        if self.is_oneline:
            self.touch_whitespace()
        else:
            self._newline = True

    def _break(self):
        if self.is_oneline:
            self.touch_whitespace()
        else:
            if not self._new_break:
                self._new_break = True
            else:
                self._new_break = False
                self._new_paragraph = True

    def paragraph(self):
        if not self.is_oneline:
            self._new_paragraph = True
        else:
            self.touch_whitespace()

    def indent(self, step=2):
        self._indentation.append(('indent', step))

    def quote(self):
        self._indentation.append(('quote', 1))

    def raw(self):
        self._indentation.append(('raw', 0))

    def oneline(self):
        self._blocks.append('oneline')

    def block(self):
        self._blocks.append('block')

    def endblock(self):
        self._blocks.pop()

    def list(self, type):
        self._newline = True
        self._lists.append(type)
        self.indent(2)

    def endlist(self):
        self._lists.pop()
        self.outdent()

    def item(self):
        self.oneline()
        return self.markup({
            'unordered':        '*',
            'arabiczero':       '0.',
            'arabic':           '1.',
            'alphalower':       'a.',
            'alphaupper':       'A.',
            'romanlower':       'i.',
            'romanupper':       'I.'
        }[self._lists[-1]] + ' ')

    def enditem(self):
        self.endblock()
        self._newline = True

    def outdent(self):
        self._indentation.pop()
    unquote = endraw = outdent

    def start_escaping(self, chars):
        self._escapes.append(chars)

    def stop_escaping(self):
        self._escapes.pop()
