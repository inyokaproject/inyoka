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

        >>> from inyoka.markup.base import RenderContext, parse
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

        >>> from inyoka.markup.base import render
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


    :copyright: (c) 2007-2020 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
