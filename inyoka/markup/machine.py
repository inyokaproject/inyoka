"""
    inyoka.markup.machine
    ~~~~~~~~~~~~~~~~~~~~~

    This implements the ast compiler and evaluator.  Most of the functionality
    here is available on the nodes itself because they mix those classes in,
    the renderer for compiled instructions is importable from the normal
    parser package.

    :copyright: (c) 2007-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from pickle import dumps, loads, HIGHEST_PROTOCOL

from django.utils.translation import gettext as _

from inyoka.utils import get_request_context


class NodeCompiler:
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
            if isinstance(item, str):
                text_buffer.append(item)
            else:
                if text_buffer:
                    result.append(''.join(text_buffer))
                    del text_buffer[:]
                result.append(item)
                is_dynamic = True
        if text_buffer:
            result.append(''.join(text_buffer))

        if not is_dynamic:
            return '!%s\0%s' % (format, ''.join(result))
        return '@' + dumps((format, result), HIGHEST_PROTOCOL)


class NodeRenderer:
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


class NodeQueryInterface:
    """
    Adds a `query` property to nodes implementing this interface.  The query
    attribute returns a new `Query` object for the node that implements the
    query interface.
    """

    @property
    def query(self):
        return Query((self,))


class Query:
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

    def __next__(self):
        return next(self._nodeiter)

    @property
    def has_any(self):
        """Return `True` if at least one node was found."""
        try:
            next(self._nodeiter)
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
                    yield from walk(node.children)
        return Query(walk(self))

    def by_type(self, type):
        """Performs an instance test on all nodes."""
        return Query(n for n in self.all if isinstance(n, type))

    def text_nodes(self):
        """Only text nodes."""
        return Query(n for n in self.all if n.is_text_node)


class RenderContext:
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

    def __init__(self, request=None, simplified=False,
                 raw=False, application=None, **kwargs):
        self.request = request
        self.simplified = simplified
        self._application = application
        self.kwargs = kwargs

    @property
    def application(self):
        if self._application is not None:
            return self._application
        return get_request_context(self.request)


class Renderer:
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
                self.instructions = [obj[pos + 1:]]
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
            if isinstance(instruction, str):
                yield instruction
            # if we are in simplified rendering mode dynamic macros
            # and other funny things are not supported. so we fail
            # silently.
            elif not context.simplified:
                allowed_context = getattr(instruction, 'allowed_context', None)
                current_context = context.application
                if (allowed_context is not None and current_context is not None
                        and current_context in allowed_context):
                    yield instruction.render(context, format)
                else:
                    from .nodes import error_box
                    box = error_box(
                        _('Invalid macro'),
                        _('This macro is not available.')
                    )
                    yield box.render(context, format)

    def render(self, context, format=None):
        """Streams into a buffer and returns it as string."""
        return ''.join(self.stream(context, format))
