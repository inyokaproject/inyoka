"""
    inyoka.markup.parsers
    ~~~~~~~~~~~~~~~~~~~~~

    Parsers can process contents inside parser blocks.  Unlike macros the
    possibilities of parsers regarding tree processing are very limited.  They
    can only return subtrees (which are inserted at the parser block position)
    or render data dynamically on page rendering.

    This means that they are also unable to both render data dynamically *and*
    emit metadata.  This functionallity is reserverd for macros.

    Beside that all features of macros also affect parsers just that they are
    passed the wrapper `data` which they can process.


    :copyright: (c) 2007-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.conf import settings
from pygments.util import ClassNotFound

from inyoka.markup import nodes
from inyoka.markup.templates import expand_page_template
from inyoka.markup.utils import debug_repr, ArgumentCollector
from inyoka.utils.highlight import highlight_code
from inyoka.utils.text import join_pagename, normalize_pagename


def get_parser(name, args, kwargs, data):
    """Instantiate a new parser or return `None` if it doesn't exist."""
    cls = ALL_PARSERS.get(name)
    if cls is None:
        return
    return cls(data, args, kwargs)


class Parser(metaclass=ArgumentCollector):
    """
    baseclass for parsers.  Concrete parsers should either subclass this or
    implement the same attributes and methods.
    """

    #: if a parser is static this has to be true.
    is_static = False

    #: True if this parser returns a block level element on dynamic
    #: rendering. This does not affect static rendering.
    is_block_tag = True

    #: the arguments this parser accepts
    arguments = ()

    __repr__ = debug_repr

    def render(self, context, format):
        """Dispatch to the correct render method."""
        rv = self.build_node(context, format)
        if isinstance(rv, str):
            return rv
        return rv.render(context, format)

    def build_node(self, context=None, format=None):
        """
        If this is a static parser this method has to return a node. If it's
        a runtime parser a context and format parameter is passed.
        """


class PygmentsParser(Parser):
    """
    Enable sourcecode highlighting.
    """

    is_static = True
    arguments = (
        ('syntax', str, 'text'),
    )

    def __init__(self, data, syntax):
        self.data = data
        self.syntax = syntax

    def build_node(self, context=None, format=None):
        try:
            rv = highlight_code(self.data, self.syntax)
        except ClassNotFound:
            rv = None
        if rv is None:
            result = [nodes.Preformatted([nodes.Text(self.data)])]
        result = [nodes.HTML(rv)]
        return nodes.Layer(class_='code', children=result)


class CSVParser(Parser):
    """
    Parse csv files and format it as table.
    """

    is_static = True

    def __init__(self, data):
        self.data = data

    def build_node(self, context=None, format=None):
        from csv import reader
        rows = reader(self.data.splitlines())
        result = nodes.Table()
        last_cells = []
        max_cells = 0
        for cells in rows:
            if not cells:
                continue
            row = nodes.TableRow()
            result.children.append(row)
            for cell in cells:
                cell = nodes.TableCell(children=[nodes.Text(cell)])
                row.children.append(cell)
            cellcount = len(cells)
            if cellcount > max_cells:
                max_cells = cellcount
            last_cells.append((cellcount, cell))
        for num, cell in last_cells:
            if num < max_cells:
                cell.colspan = max_cells - num + 1
        return result


class TemplateParser(Parser):
    """
    Works exactly like the template macro just with the difference that
    the body of the parser is passed as first argument.

    As such the following two pieces of code do the very same::

        [[Vorlage(Foo, "
            Hello World
        ")]]

        {{{
        #!Vorlage Foo
        Hello World
        }}}
    """

    has_argument_parser = True
    is_static = True

    def __init__(self, data, args, kwargs):
        if not args:
            self.template = None
            self.context = None
            return
        items = list(kwargs.items())
        for idx, arg in enumerate(args[1:] + (data,)):
            items.append(('arguments.%d' % idx, arg))
        self.template = join_pagename(settings.WIKI_TEMPLATE_BASE,
                                      normalize_pagename(args[0], False))
        self.context = items

    def build_node(self, context=None, format=None):
        return expand_page_template(self.template, self.context, True)


#: list of all parsers this wiki can handle
ALL_PARSERS = {
    'code': PygmentsParser,
    'csv': CSVParser,
    'vorlage': TemplateParser
}
