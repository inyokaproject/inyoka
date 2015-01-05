# -*- coding: utf-8 -*-
"""
    inyoka.markup
    ~~~~~~~~~~~~~

    The package implements a rather complex parsers for the inyoka wiki
    syntax.  The parser is roughly divided into five more or less independent
    parts:

    - `Lexer` -- tokenizes the markup into tokens, holds in internal stack
      that resolves mismatched elements.

    - `Parser` -- fetches tokens from the lexer and creates nodes.
      Additionally it calls the transformers after that tree was created.

    - `Node` -- multile nodes make a tree.  A tree is renderable into multiple
      output formats, however HTML is the only supported at the moment.

    - `Transformer` -- the transformers postprocess the syntax tree.  This is
      necessary for typography, smiley insertions, paragraphs etc.

    - `machine` -- the machine is the compiler and renderer.  The compiler
      just takes the flattened stream from the node tree and compiles it into
      a format the renderer can process.  The renderer is then able to
      generate HTML or whatever from the compiler.  If caching is not wanted
      for a specific output format the compilation step can be omitted and the
      renderer fetches the instructions directly from the node tree's prepared
      stream.

      Parts of the machine are mixed into the nodes so you can renders nodes
      directly without additional imports.


    Example usage
    -------------

    If you want to work with the node tree you just have to parse something::

        >>> from inyoka.markup import parse, RenderContext
        >>> context = RenderContext()
        >>> node = parse("Hello World!\\n\\n''foo bar spam''")

    Rendering works directly from the node if you don't want to cache it::

        >>> node.render(context, 'html')
        u'<p>Hello World!</p><p><em>foo bar spam</em></p>'

    You can also stream it into a generator that yields the result step by
    step::

        >>> gen = node.stream(context, 'html')
        >>> gen.next()
        u'<p>'
        >>> gen.next()
        u'Hello World!'
        >>> gen.next()
        u'</p>'

    Or compile it::

        >>> code = node.compile('html')

    And then render the compiled string using `render()`::

        >>> from inyoka.markup import render
        >>> render(code, context)
        u'<p>Hello World!</p><p><em>foo bar spam</em></p>'

    The compiler ensures that dynamic elements like runtime macros or parsers
    are called during rendering, not during compiling.  This gives us the
    possibility to cache things in the cached stream.

    The code format is either a static string with a header prefix or a
    pickled list with references to dynamic elements.  It may and will most
    likely contain binary data, thus it should not be saved in the database.


    Syntax
    ------

    The syntax we use is derived from the MoinMoin engine's syntax.  In fact
    this parser tries to stay as compatible as possible while fixing some of
    the problem that exist in the moin syntax.

    This (from an implementors point of view) most obvious difference is that
    the inyoka.markup is not line based although many syntax elements are
    newline aware.  One of the syntax elements that end at a newline are for
    example list items.  If however inline markup (such as bold text) is left
    opened the list item will not close until the bold markup is closed first.

    We require that because the lexer does not know anything about block or
    inline elements.  That said it becomes obvious that paragraph handling is
    not part of the lexing process but patched into the syntax tree after the
    parsing process.  This allows use to generate more valid HTML because we
    can avoid adding paragraphs to inline elements or macros.

    Differences to MoinMoin
    ~~~~~~~~~~~~~~~~~~~~~~~

    -   Elements must be closed and cannot spawn multiple paragraphs
    -   Macros, parsers, table definitions and some other syntax elements
        that allow arguments have an fixed argument syntax:  a list of
        arguments, whitespace or comma keeps arguments apart and if you
        put single quotes around multiple arguments (escaped with doubling
        quotes) preserves whitespace.  Inside such strings one can even
        use the macro delimiters. (``[[Macro('[[Foo()]]')]]`` is valid)
    -   Blockquotes are supported and can contain any kind of markup.  The
        syntax is derived from ASCII Mails: ``> quoted text here``.

    Additionally all the keyword parameters are translated to German for
    obvious reasons.  Keep in mind that Moin changed the syntax from 1.6
    to 1.7 and this parsers is not (yet?) compatible with the latter.


    Meta Data
    ---------

    The syntax tree has support for metadata.  After parsing metadata from the
    tree is combined (at least by the wiki system) with other metadata and
    stored in the database.  For example the tree is traversed for any
    `nodes.MetaData` and `InternalLink` nodes.  Not every component in the
    inyoka systems makes use of metadata and they can ignore those nodes
    completely.  Their text and rendering representation is empty.

    However if metadata is used it's important to *walk* the tree, not just
    look for `nodes.MetaData` at toplevel.  It's true that the metadata
    comment syntax is only parsed at top level but there are elements that
    support nested markup such as quote tags.  Also macros and parsers that
    are expanded at parse time can return `nodes.MetaData` metadata.


    :copyright: (c) 2007-2015 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import unicodedata
import re
from urlparse import urlsplit
from functools import partial

from django.utils.translation import ugettext as _

from inyoka.markup import nodes
from inyoka.markup.constants import HTML_COLORS
from inyoka.markup.lexer import Lexer, escape
from inyoka.markup.machine import Renderer, RenderContext
from inyoka.markup.transformers import DEFAULT_TRANSFORMERS
from inyoka.markup.utils import filter_style
from inyoka.utils.urls import href

__all__ = ['parse', 'render', 'stream', 'escape']


# the maximum depth of stack-protected nodes
MAXIMUM_DEPTH = 200

def _ikhaya_id(x):
    try:
        id = int(x)
        return href('portal', 'ikhaya', id)
    except ValueError:
        return href('ikhaya', x)

# the default inter-"wiki"s
STANDARD_WIKI_MAP = {
    'user': lambda x: href('portal', 'user', x),
    'paste': lambda x: href('pastebin', x),
    'topic': lambda x: href('forum', 'topic', x),
    'ikhaya': _ikhaya_id,
    'search': lambda x: href('portal', 'search', query=x),
    'post': lambda x: href('forum', 'post', x),
}

_hex_color_re = re.compile(r'#([a-f0-9]{3}){1,2}$')

_table_align_re = re.compile(r'''(?x)
    (-(?P<colspan>\d+)) |
    (\|(?P<rowspan>\d+)) |
    (?P<left>\() |
    (?P<right>\)) |
    (?P<center>:) |
    (?P<top>\^) |
    (?P<middle>\~) |
    (?P<bottom>v)
''')


def parse(markup, wiki_force_existing=False, catch_stack_errors=True,
          transformers=None):
    """Parse markup into a node."""
    try:
        return Parser(markup, transformers, wiki_force_existing).parse()
    except StackExhaused:
        if not catch_stack_errors:
            raise
        return nodes.Paragraph([
            nodes.Strong([nodes.Text(_(u'Internal error: '))]),
            nodes.Text(_(u'The parser found too deeply nested elements.'))
        ])


def render(instructions, context=None, format=None):
    """Render the compiled instructions."""
    if context is None:
        context = RenderContext()
    return Renderer(instructions).render(context, format)


def stream(instructions, context=None, format=None):
    """Stream the compiled instructions."""
    if context is None:
        context = RenderContext()
    return Renderer(instructions).stream(context, format)


def unescape_string(string):
    """
    Unescape a string with python semantics but silent fallback.
    """
    result = []
    write = result.append
    simple_escapes = {
        'a': '\a',
        'n': '\n',
        'r': '\r',
        'f': '\f',
        't': '\t',
        'v': '\v',
        '\\': '\\',
        '"': '"',
        "'": "'",
        '0': '\x00'
    }
    unicode_escapes = {
        'x': 2,
        'u': 4,
        'U': 8
    }
    chariter = iter(string)
    next_char = chariter.next

    try:
        for char in chariter:
            if char == '\\':
                char = next_char()
                if char in simple_escapes:
                    write(simple_escapes[char])
                elif char in unicode_escapes:
                    seq = [next_char() for x in xrange(unicode_escapes[char])]
                    try:
                        write(unichr(int(''.join(seq), 16)))
                    except ValueError:
                        pass
                elif char == 'N' and next_char() != '{':
                    seq = []
                    while True:
                        char = next_char()
                        if char == '}':
                            break
                        seq.append(char)
                    try:
                        write(unicodedata.lookup(u''.join(seq)))
                    except KeyError:
                        pass
                else:
                    write('\\' + char)
            else:
                write(char)
    except StopIteration:
        pass
    return u''.join(result)


def _parse_align_args(args, kwargs):
    """
    A helper function that parses position arguments for the table syntax.
    It's passed an `args` tuple and `kwargs` dict and will return a dict with
    the parsed attributes (and a copy of the `kwargs`) and a list of
    position arguments not yet handled.

    Common idom::

        attributes, args = _parse_align_args(args, kwargs)

    After that you can savely ignore kwargs.
    """
    attributes = kwargs.copy()
    args_left = []
    for arg in args:
        pos = 0
        while pos < len(arg):
            m = _table_align_re.match(arg, pos)
            if m is None:
                args_left.append(arg[pos:])
                break
            args = m.groupdict()
            pos = m.end()

            for x in 'colspan', 'rowspan':
                if args[x] is not None:
                    attributes[x] = int(args[x])
                    break
            else:
                for x in 'left', 'right', 'center':
                    if args[x] is not None:
                        attributes['align'] = x
                        break
                else:
                    for x in 'top', 'middle', 'bottom':
                        if args[x] is not None:
                            attributes['valign'] = x
                            break

    return attributes, args_left


class StackExhaused(ValueError):
    """
    Raised if the parser recognizes nested structures that would hit the
    stack limit.
    """


class Parser(object):
    """
    The wiki syntax parser.  Never use this class directly, always do this
    via the public `parse()` function of this module.  The behavior of this
    class in multithreaded environments is undefined (might change from
    revision to revision) and the `parse()` function knows how to handle that.
    Either be reusing parsers if safe, locking or reinstanciating.

    This parser should be considered a private class.  All of the attributes
    and methods exists for the internal parsing process.  As long as you don't
    extend the parser you should only use the `parse()` function (except of
    parser unittests which can savely user the `Parser` class itself).
    """

    def __init__(self, string, transformers=None, wiki_force_existing=False):
        """
        In theory you never have to instanciate this parser yourself because
        the high level `parse()` function encapsulates this.  However for the
        unittests it's important to be able to disable and enable the
        `transformers` by hand.  If you don't provide any transformers the
        default transformers are used.
        """
        self.string = string
        self.lexer = Lexer()
        self.stack_depth = 0
        if transformers is None:
            transformers = DEFAULT_TRANSFORMERS[:]
        self.transformers = transformers
        self.wiki_force_existing = wiki_force_existing

        #: node dispatchers
        self._handlers = {
            'text': self.parse_text,
            'raw': self.parse_raw,
            'nl': self.parse_nl,
            'highlighted_begin': self.parse_highlighted,
            'highlighted_wi_begin': partial(self.parse_highlighted,
                                            name='highlighted_wi'),
            'conflict_begin': self.parse_conflict_left,
            'conflict_switch': self.parse_conflict_middle,
            'conflict_end': self.parse_conflict_end,
            'metadata_begin': self.parse_metadata,
            'headline_begin': self.parse_headline,
            'strong_begin': self.parse_strong,
            'emphasized_begin': self.parse_emphasized,
            'escaped_code_begin': self.parse_escaped_code,
            'code_begin': self.parse_code,
            'underline_begin': self.parse_underline,
            'stroke_begin': self.parse_stroke,
            'small_begin': self.parse_small,
            'big_begin': self.parse_big,
            'sub_begin': self.parse_sub,
            'sup_begin': self.parse_sup,
            'footnote_begin': self.parse_footnote,
            'color_begin': self.parse_color,
            'size_begin': self.parse_size,
            'font_begin': self.parse_font,
            'mod_begin': self.parse_mod,
            'edit_begin': self.parse_edit,
            'quote_begin': self.parse_quote,
            'list_item_begin': self.parse_list,
            'definition_begin': self.parse_definition,
            'wiki_link_begin': self.parse_wiki_link,
            'external_link_begin': self.parse_external_link,
            'free_link': self.parse_free_link,
            'ruler': self.parse_ruler,
            'macro_begin': self.parse_macro,
            'template_begin': self.parse_template,
            'pre_begin': self.parse_pre_block,
            'table_row_begin': self.parse_table,
            'box_begin': self.parse_box,
            'sourcelink': self.parse_source_link
        }

        #: runtime information
        self.is_dirty = False
        self.deferred_macros = {
            'final': [],
            'initial': [],
            'late': []
        }

    def parse_node(self, stream):
        """
        Call this with a `TokenStream` to dispatch to the correct parser call.
        If the current token on the stream is not handleable it will raise a
        `KeyError`.  However you should not relay on that behavior because the
        beavior is undefined and may change.  It's your reposibility to make
        sure the parser never calls `parse_node` on not existing nodes when
        extending the lexer / parser.
        """
        # stack exhausted, return a node that represents that
        if self.stack_depth >= MAXIMUM_DEPTH:
            raise StackExhaused()
        self.stack_depth += 1
        try:
            return self._handlers[stream.current.type](stream)
        finally:
            self.stack_depth -= 1

    def parse_text(self, stream):
        """Expects a ``'text'`` token and returns a `nodes.Text`."""
        return nodes.Text(stream.expect('text').value)

    def parse_raw(self, stream):
        """Parse a raw marked section."""
        return nodes.Raw([nodes.Text(stream.expect('raw').value)])

    def parse_nl(self, stream):
        """Expects a ``'nl'`` token and returns a `nodes.Newline`."""
        stream.expect('nl')
        return nodes.Newline()

    def parse_highlighted(self, stream, name='highlighted'):
        """Parse a highlighted section."""
        stream.expect('%s_begin' % name)
        children = []
        while stream.current.type != '%s_end' % name:
            children.append(self.parse_node(stream))
        stream.expect('%s_end' % name)
        return nodes.Highlighted(children)

    def parse_conflict_left(self, stream):
        """The begin conflict marker."""
        stream.expect('conflict_begin')
        return nodes.ConflictMarker('left')

    def parse_conflict_middle(self, stream):
        """The middle conflict marker."""
        stream.expect('conflict_switch')
        return nodes.ConflictMarker('middle')

    def parse_conflict_end(self, stream):
        """The end conflict marker."""
        stream.expect('conflict_end')
        return nodes.ConflictMarker('right')

    def parse_metadata(self, stream):
        """
        We do support inline metadata on a syntax level too.  A metadata
        section starts with *one* leading hash until the end of the line.  If
        the lexer stumbles upon something like that it emits a
        ``'metadata_begin'`` token this parsing function uses.  It's important
        to know that this can yield metadata at arbitrary positions if quoted
        for example.

        Returns a `nodes.MetaData` object.
        """
        stream.expect('metadata_begin')
        key = stream.expect('metadata_key').value
        args, kwargs = self.parse_arguments(stream, 'metadata_end')
        stream.expect('metadata_end')
        assert not kwargs
        return nodes.MetaData(key, args)

    def parse_headline(self, stream):
        """
        Parse a headline.  Unlike MoinMoin with inline formatting and a
        variable length headline closing section.

        Returns a `Headline` node.
        """
        token = stream.expect('headline_begin')
        children = []
        while stream.current.type != 'headline_end':
            children.append(self.parse_node(stream))
        stream.expect('headline_end')
        return nodes.Headline(len(token.value.strip()), children=children)

    def parse_strong(self, stream):
        """
        Parse strong emphasized text.

        Returns a `Strong` node.
        """
        stream.expect('strong_begin')
        children = []
        while stream.current.type != 'strong_end':
            children.append(self.parse_node(stream))
        stream.expect('strong_end')
        return nodes.Strong(children)

    def parse_emphasized(self, stream):
        """
        Parse normal emphasized text.

        Returns a `Emphasized` node.
        """
        stream.expect('emphasized_begin')
        children = []
        while stream.current.type != 'emphasized_end':
            children.append(self.parse_node(stream))
        stream.expect('emphasized_end')
        return nodes.Emphasized(children)

    def parse_escaped_code(self, stream):
        """
        This parses escaped code formattings.  Escaped code formattings work
        like normal code formattings but their delimiter backticks are doubled
        so that one can use single backticks inside.

        Returns a `Code` node.
        """
        stream.expect('escaped_code_begin')
        buffer = []
        while stream.current.type != 'escaped_code_end':
            buffer.append(stream.current.value)
            stream.next()
        stream.expect('escaped_code_end')
        return nodes.Code([nodes.Text(u''.join(buffer))], class_='notranslate')

    def parse_code(self, stream):
        """
        Parse inline code, don't confuse that with `parse_pre_block`.

        Returns a `Code` node.
        """
        stream.expect('code_begin')
        buffer = []
        while stream.current.type == 'text':
            buffer.append(stream.current.value)
            stream.next()
        stream.expect('code_end')
        return nodes.Code([nodes.Text(u''.join(buffer))], class_='notranslate')

    def parse_underline(self, stream):
        """
        Parses the underline formatting.  This should really go away or change
        the meaning to *inserted* text in which situation this makes sense.

        Returns a `Underline` node.
        """
        stream.expect('underline_begin')
        children = []
        while stream.current.type != 'underline_end':
            children.append(self.parse_node(stream))
        stream.expect('underline_end')
        return nodes.Underline(children)

    def parse_stroke(self, stream):
        """
        Parse deleted text.

        Returns a `Stroke` node.
        """
        stream.expect('stroke_begin')
        children = []
        while stream.current.type != 'stroke_end':
            children.append(self.parse_node(stream))
        stream.expect('stroke_end')
        return nodes.Stroke(children)

    def parse_small(self, stream):
        """
        Parse belittled text.

        Returns a `Small` node.
        """
        stream.expect('small_begin')
        children = []
        while stream.current.type != 'small_end':
            children.append(self.parse_node(stream))
        stream.expect('small_end')
        return nodes.Small(children)

    def parse_big(self, stream):
        """
        Parse augmented text.

        Returns a `Big` node.
        """
        stream.expect('big_begin')
        children = []
        while stream.current.type != 'big_end':
            children.append(self.parse_node(stream))
        stream.expect('big_end')
        return nodes.Big(children)

    def parse_sub(self, stream):
        """
        Parse text in subscript.

        Returns a `Sub` node.
        """
        stream.expect('sub_begin')
        children = []
        while stream.current.type != 'sub_end':
            children.append(self.parse_node(stream))
        stream.expect('sub_end')
        return nodes.Sub(children)

    def parse_sup(self, stream):
        """
        Parse text in supscript.

        Returns a `Sup` node.
        """
        stream.expect('sup_begin')
        children = []
        while stream.current.type != 'sup_end':
            children.append(self.parse_node(stream))
        stream.expect('sup_end')
        return nodes.Sup(children)

    def parse_footnote(self, stream):
        """
        Parses an inline footnote declaration.  This doesn't make it a
        footnote though, for that tasks a `FootnoteSupport` transformer
        exists.  The default rendering is just parenthized small text
        at the same position.

        Returns a `Footnote` node.
        """
        stream.expect('footnote_begin')
        children = []
        while stream.current.type != 'footnote_end':
            children.append(self.parse_node(stream))
        stream.expect('footnote_end')
        return nodes.Footnote(children)

    def parse_color(self, stream):
        """
        Parse a color definition.  This exists for backwards compatibility
        with phpBB.

        Returns a `Color` node.
        """
        stream.expect('color_begin')
        color = stream.expect('color_value').value.strip().lower()
        if not _hex_color_re.match(color):
            if color in HTML_COLORS:
                color = HTML_COLORS[color]
            else:
                color = '#000000'
        children = []
        while stream.current.type != 'color_end':
            children.append(self.parse_node(stream))
        stream.expect('color_end')
        return nodes.Color(color, children)

    def parse_size(self, stream):
        """
        Parse a size tag.  This exists for backwards compatibility with phpBB.

        Returns a `Size` node.
        """
        stream.expect('size_begin')
        size = stream.expect('font_size').value.strip()
        try:
            size = int(100.0 / 14 * float(size))
        except ValueError:
            size = 100
        children = []
        while stream.current.type != 'size_end':
            children.append(self.parse_node(stream))
        stream.expect('size_end')
        return nodes.Size(size, children)

    def parse_font(self, stream):
        """
        Parse a font tag.  This exists for backwards compatibility with phpBB.

        Returns a `Font` node.
        """
        stream.expect('font_begin')
        face = stream.expect('font_face').value.strip()
        children = []
        while stream.current.type != 'font_end':
            children.append(self.parse_node(stream))
        stream.expect('font_end')
        return nodes.Font([face], children)

    def parse_mod(self, stream):
        """
        Parse a mod tag.

        Returns a `Moderated` node.
        """
        stream.expect('mod_begin')
        username = stream.expect('username').value.strip()
        children = []
        while stream.current.type != 'mod_end':
            children.append(self.parse_node(stream))
        stream.expect('mod_end')
        return nodes.Moderated(username, children)

    def parse_edit(self, stream):
        """
        Parse an edit tag.

        Returns an `Edited` node.
        """
        stream.expect('edit_begin')
        username = stream.expect('username').value.strip()
        children = []
        while stream.current.type != 'edit_end':
            children.append(self.parse_node(stream))
        stream.expect('edit_end')
        return nodes.Edited(username, children)

    def parse_quote(self, stream):
        """
        Parse a quoted block (blockquote).  It does not set the typographic
        quotes you might have expected.  That's part of the `GermanTypography`
        transformer.

        Returns a `Quote` node.
        """
        stream.expect('quote_begin')
        children = []
        while stream.current.type != 'quote_end':
            children.append(self.parse_node(stream))
        stream.expect('quote_end')
        return nodes.Quote(children)

    def parse_list(self, stream):
        """
        This parses a list or a list of lists.  Due to the fail silent
        approach of the syntax this fixes some common errors.  For example
        a list that follows a list with a different type and no paragraph
        inbetween is considered being a different list.

        Returns a `List` node.
        """
        def check_item(token):
            full = token.value.expandtabs()
            stripped = full.lstrip()
            indentation = len(full) - len(stripped)
            return indentation, ('unordered', 'unordered', 'arabiczero',
                               'arabic', 'alphalower', 'alphaupper',
                               'romanlower', 'romanupper'
                               )['*-01aAiI'.index(stripped[0])]

        indentation, list_type = check_item(stream.current)
        result = nodes.List(list_type)

        while stream.current.type == 'list_item_begin':
            new_indentation, new_list_type = check_item(stream.current)
            if (list_type != new_list_type and
                new_indentation == indentation) or new_indentation < indentation:
                break
            elif new_indentation > indentation:
                nested_list = self.parse_list(stream)
                if result.children:
                    result.children[-1].children.append(nested_list)
                else:
                    result.children.append(nodes.ListItem([nested_list]))
                continue
            stream.next()
            children = []
            while stream.current.type != 'list_item_end':
                children.append(self.parse_node(stream))
            if children:
                result.children.append(nodes.ListItem(children))
            stream.next()
        return result

    def parse_definition(self, stream):
        """
        Parses a definition list.

        Returns a `DefinitionList` node.
        """
        stream.expect('definition_begin')
        result = nodes.DefinitionList()

        while not stream.eof:
            term = stream.expect('definition_term').value
            children = []
            while stream.current.type != 'definition_end':
                children.append(self.parse_node(stream))
            result.children.append(nodes.DefinitionTerm(term, children))
            if stream.current.type == 'definition_end':
                stream.next()
                if stream.current.type == 'definition_begin':
                    stream.next()
                else:
                    break
        return result

    def parse_wiki_link(self, stream):
        """
        Parses an wiki or interwiki link.  Depending on the syntax the
        returned link is either an `InternalLink` node, an `Link` node or
        an `InternalWikiLink` node.
        """
        stream.expect('wiki_link_begin')
        wiki, page = stream.expect('link_target').value
        page = page.replace('\:', ':')
        if '#' in page:
            page, anchor = page.split('#', 1)
        else:
            anchor = None
        children = []
        while stream.current.type != 'wiki_link_end':
            children.append(self.parse_node(stream))
        stream.expect('wiki_link_end')
        if not wiki:
            return nodes.InternalLink(page, children, anchor=anchor,
                                      force_existing=self.wiki_force_existing)
        elif wiki in STANDARD_WIKI_MAP:
            if not children:
                children = [nodes.Text(page)]
            return nodes.Link(STANDARD_WIKI_MAP[wiki](page), children,
                              class_=wiki)
        return nodes.InterWikiLink(wiki, page, children, anchor=anchor)

    def parse_external_link(self, stream):
        """
        Parses an external link.

        Returns a `Link` node.
        """
        stream.expect('external_link_begin')
        url = stream.expect('link_target').value
        children = []
        while stream.current.type != 'external_link_end':
            children.append(self.parse_node(stream))
        stream.expect('external_link_end')
        return nodes.Link(url, children)

    def parse_free_link(self, stream):
        """
        Parses an free link.

        Returns a `Link` node.
        """
        target = stream.expect('free_link').value
        try:
            urlsplit(target)
        except ValueError:
            return nodes.Text(target)
        return nodes.Link(target, shorten=True)

    def parse_ruler(self, stream):
        """
        Parses a horizontal ruler.

        Returns a `Ruler` node.
        """
        stream.expect('ruler')
        return nodes.Ruler()

    def parse_macro(self, stream):
        """
        Parse a macro declaration.  It's important to know that macros are
        expanded already in the parsing process.  Depending on the type the
        macros specify the macro is then either inserted into the parse tree
        (default behavior) or marked as deferred and processed after the main
        parsing (or after the transformers).

        If a macro is expanded at rendering time a `nodes.Macro` is returned
        that holds the already instanciated macro.  Because the macro *is*
        instanciate, dynamic macros have to ensure that they support pickle.
        """
        stream.expect('macro_begin')
        name = stream.expect('macro_name').value
        args, kwargs = self.parse_arguments(stream, 'macro_end')
        stream.next()
        # FIXME: Circular Imports
        from inyoka.markup.macros import get_macro
        macro = get_macro(name, args, kwargs)
        if macro is None:
            return nodes.error_box(
                _(u'Missing macro'),
                _(u'The macro “%(name)s” does not exist.') % {'name': name})
        elif macro.is_tree_processor:
            placeholder = nodes.DeferredNode(macro)
            self.deferred_macros[macro.stage].append((placeholder, macro))
            return placeholder
        elif macro.is_static:
            return macro.build_node()
        return nodes.Macro(macro)

    def parse_template(self, stream):
        """Parse the template macro shortcut."""
        # FIXME: Circular imports
        from inyoka.wiki.macros import Template
        stream.expect('template_begin')
        name = stream.expect('template_name').value
        args, kwargs = self.parse_arguments(stream, 'template_end')
        stream.next()
        return Template((name,) + args, kwargs).build_node()

    def parse_pre_block(self, stream):
        """
        Parse a pre block or parser block.  If a shebang is present the parser
        with that name is instanciated and expanded, if it's a dynamic parser
        a `Parser` node will be returned.

        If no shebang is present or a parser with that name does not exist the
        data is handled as preformatted block data and a `Preformatted` node
        is returned.
        """
        # FIXME: Circular imports
        from inyoka.markup.parsers import get_parser
        stream.expect('pre_begin')
        if stream.current.type == 'parser_begin':
            name = stream.current.value
            stream.next()
            args, kwargs = self.parse_arguments(stream, 'parser_end')
            if stream.current.type != 'pre_end':
                stream.next()
        else:
            name = None

        children = []
        text_node = None
        while stream.current.type != 'pre_end':
            node = self.parse_node(stream)
            if node.is_text_node:
                if text_node is None and node.text[:1] == '\n':
                    node.text = node.text[1:]
                text_node = node
            children.append(node)
        if text_node is not None and text_node.text[-1:] == '\n':
            text_node.text = text_node.text[:-1]
        stream.expect('pre_end')

        if name is None:
            return nodes.Preformatted(children, class_='notranslate')

        data = u''.join(x.text for x in children)
        parser = get_parser(name, args, kwargs, data)
        if parser is None:
            return nodes.Preformatted([nodes.Text(data)], class_='notranslate')
        elif parser.is_static:
            return parser.build_node()
        return nodes.Parser(parser)

    def parse_table(self, stream):
        """
        Parse a table.  Contrary to moin we have extended support for
        attribute sections (``<foo, bar=baz>``) which means that table
        delimiters are supported inside that section.  Also all attributes
        in such a section are German.

        Returns a `Table` node.
        """
        def attach_defs():
            if stream.current.type in 'table_def_begin':
                stream.next()
                args, kwargs = self.parse_arguments(stream, 'table_def_end')
                if stream.current.type == 'table_def_end':
                    stream.next()
                attrs, args = _parse_align_args(args, kwargs)
                if cell_type == 'tablefirst':
                    table.class_ = attrs.get('tableclass') or None
                    table.style = filter_style(attrs.get('tablestyle')) or None
                if cell_type in ('tablefirst', 'rowfirst'):
                    row.class_ = attrs.get('rowclass') or None
                    if not row.class_:
                        row.class_ = u' '.join(args) or None
                    row.style = filter_style(attrs.get('rowstyle')) or None
                cell.class_ = attrs.get('cellclass') or None
                cell.style = filter_style(attrs.get('cellstyle')) or None
                cell.colspan = attrs.get('colspan', 0)
                cell.rowspan = attrs.get('rowspan', 0)
                cell.align = attrs.get('align')
                if cell.align not in ('left', 'right', 'center'):
                    cell.align = None
                cell.valign = attrs.get('valign')
                if cell.valign not in ('top', 'middle', 'bottom'):
                    cell.valign = None
                if cell_type == 'normal':
                    if not cell.class_:
                        cell.class_ = u' '.join(args) or None

        table = nodes.Table()
        cell = row = None
        cell_type = 'tablefirst'
        while not stream.eof:
            if stream.current.type == 'table_row_begin':
                stream.next()
                cell = nodes.TableCell()
                row = nodes.TableRow([cell])
                table.children.append(row)
                attach_defs()
            elif stream.current.type == 'table_col_switch':
                stream.next()
                cell_type = 'normal'
                cell = nodes.TableCell()
                row.children.append(cell)
                attach_defs()
            elif stream.current.type == 'table_row_end':
                stream.next()
                cell_type = 'rowfirst'
                if stream.current.type != 'table_row_begin':
                    break
            else:
                cell.children.append(self.parse_node(stream))
        return table

    def parse_box(self, stream):
        """
        Parse a box.  Pretty much like a table with one cell that renders to
        a div or a div with a title and body.

        Returns a `Box` node.
        """
        box = nodes.Box()
        stream.expect('box_begin')
        if stream.current.type == 'box_def_begin':
            stream.next()
            args, kwargs = self.parse_arguments(stream, 'box_def_end')
            if stream.current.type == 'box_def_end':
                stream.next()
            attrs, args = _parse_align_args(args, kwargs)
            box.align = attrs.get('align')
            if box.align not in ('left', 'right', 'center'):
                box.align = None
            box.align = attrs.get('valign')
            if box.valign not in ('top', 'middle', 'bottom'):
                box.valign = None
            box.class_ = attrs.get('klasse')
            if not box.class_:
                box.class_ = u' '.join(args)
            box.style = filter_style(attrs.get('style')) or None
            box.title = attrs.get('title')
            box.class_ = attrs.get('class')

        while stream.current.type != 'box_end':
            box.children.append(self.parse_node(stream))
        stream.expect('box_end')
        return box

    def parse_arguments(self, stream, end_token):
        """
        Helper function for function argument parsing.  Pass it a
        `TokenStream` and the delimiter token for the argument section and
        it will extract all position and keyword arguments.

        Returns a ``(args, kwargs)`` tuple.
        """
        args = []
        kwargs = {}
        keywords = []
        while stream.current.type != end_token:
            if stream.current.type in ('func_string_arg', 'text'):
                if stream.current.type == 'text':
                    value = stream.current.value
                else:
                    value = unescape_string(stream.current.value[1:-1])
                stream.next()
                if keywords:
                    for keyword in keywords:
                        kwargs[keyword] = value
                    del keywords[:]
                else:
                    args.append(value)
            elif stream.current.type == 'text':
                args.append(stream.current.value)
                stream.next()
            elif stream.current.type == 'func_kwarg':
                keywords.append(stream.current.value)
                stream.next()
            elif stream.current.type == 'func_argument_delimiter':
                stream.next()
            else:
                break
        for keyword in keywords:
            args.append(keyword)
        return tuple(args), kwargs

    def expand_macros(self, tree, stage):
        """
        Helper function for macro expansion.  This is called at the end of
        the parsing process to insert deferred macros.
        """
        for placeholder, macro in self.deferred_macros[stage]:
            placeholder.become(macro.build_node(tree))

    def parse(self):
        """
        Starts the parsing process.  This sets the dirty flag which means that
        you have to create a new parser after the parsing.
        """
        if self.is_dirty:
            raise RuntimeError('the parser is dirty. reinstanciate it.')
        self.is_dirty = True
        stream = self.lexer.tokenize(self.string)
        result = nodes.Document()
        while not stream.eof:
            result.children.append(self.parse_node(stream))
        for stage in 'initial', 'late':
            self.expand_macros(result, stage)
        for transformer in self.transformers:
            result = transformer.transform(result)
        self.expand_macros(result, 'final')
        return result

    def parse_source_link(self, stream):
        """
        Parse a link to a source [1] etc.
        """
        sourcenumber = stream.expect('sourcelink').value
        return nodes.SourceLink(int(sourcenumber))
