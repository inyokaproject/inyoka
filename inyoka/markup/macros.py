# -*- coding: utf-8 -*-
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


    :copyright: (c) 2007-2012 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import os
import operator
import itertools
from datetime import datetime
from django.conf import settings
from django.utils.translation import ugettext as _
from inyoka.utils.urls import href, url_for
from inyoka.portal.models import StaticFile
from inyoka.forum.models import Attachment as ForumAttachment
from inyoka.markup import nodes
from inyoka.markup.utils import debug_repr, dump_argstring, ArgumentCollector
from inyoka.markup.templates import expand_page_template
from inyoka.wiki.views import fetch_real_target
from inyoka.wiki.signals import build_picture_node
from inyoka.markup.utils import filter_style
from inyoka.utils.urls import is_external_target
from inyoka.utils.text import join_pagename, normalize_pagename
from inyoka.utils.dates import parse_iso8601, format_datetime
from inyoka.utils.imaging import get_thumbnail, parse_dimensions


ALL_MACROS = {}


def get_macro(name, args, kwargs):
    """
    Instanciate a new macro or return `None` if it doesn't exist.  This is
    used by the parser when it encounters a `macro_begin` token.  Usually
    there is no need to call this function from outside the parser.  There
    may however be macros that want to extend the functionallity of an
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
            raise RuntimeError(u'Macro name "%s" already registered' % name)
        ALL_MACROS[name] = cls


class Macro(object):
    """
    Baseclass for macros.  All macros should extend from that or implement
    the same attributes.  The preferred way however is subclassing.
    """

    __metaclass__ = ArgumentCollector

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

    __repr__ = debug_repr

    @property
    def argument_string(self):
        """The argument string."""
        return dump_argstring(self.argument_def)

    def render(self, context, format):
        """Dispatch to the correct render method."""
        rv = self.build_node(context, format)
        if isinstance(rv, basestring):
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

    names = (u'TableOfContents', u'Inhaltsverzeichnis')
    stage = 'final'
    is_block_tag = True
    arguments = (
        ('max_depth', int, 3),
        ('type', {
            'unordered':    'unordered',
            'arabic0':      'arabiczero',
            'arabic':       'arabic',
            'alphabeth':    'alphalower',
            'ALPHABETH':    'alphaupper',
            'roman':        'romanlower',
            'ROMAN':        'romanupper'
        }, 'arabic')
    )

    def __init__(self, depth, list_type):
        self.depth = depth
        self.list_type = list_type

    def build_node(self, tree):
        result = nodes.List(self.list_type)
        stack = [result]
        normalized_level = 0
        last_level = 0
        for headline in tree.query.by_type(nodes.Headline):
            if not headline.level == last_level:
                if headline.level > normalized_level:
                    normalized_level += 1
                elif headline.level < normalized_level:
                    normalized_level -= (normalized_level - headline.level)
            if normalized_level > self.depth:
                continue
            elif normalized_level > len(stack):
                for x in xrange(normalized_level - len(stack)):
                    node = nodes.List(self.list_type)
                    if stack[-1].children:
                        stack[-1].children[-1].children.append(node)
                    else:
                        result.children.append(nodes.ListItem([node]))
                    stack.append(node)
            elif normalized_level < len(stack):
                for x in xrange(len(stack) - normalized_level):
                    stack.pop()
            ml = normalized_level*((45-self.depth-normalized_level)/(normalized_level or 1))
            text = len(headline.text)>ml and headline.text[:ml]+'...' or \
                   headline.text
            caption = [nodes.Text(text)]
            link = nodes.Link('#' + headline.id, caption)
            stack[-1].children.append(nodes.ListItem([link]))
            last_level = headline.level
        head = nodes.Layer(children=[nodes.Text(_(u'Table of contents'))],
                           class_='head')
        result = nodes.Layer(class_='toc toc-depth-%d' % self.depth,
                             children=[head, result])
        return result


class Picture(Macro):
    """
    This macro can display external images and attachments as images.  It
    also takes care about thumbnail generation.  For any internal (attachment)
    image included that way an ``X-Attach`` metadata is emitted.

    Like for any link only absolute targets are allowed.  This might be
    surprising behavior if you're used to the MoinMoin syntax but caused
    by the fact that the parser does not know at parse time on which page
    it is operating.
    """
    names = (u'Picture', u'Bild')
    arguments = (
        ('picture', unicode, u''),
        ('size', unicode, u''),
        ('align', unicode, u''),
        ('alt', unicode, None),
        ('title', unicode, None)
    )

    def __init__(self, target, dimensions, alignment, alt, title):
        self.metadata = [nodes.MetaData('X-Attach', [target])]
        self.width, self.height = parse_dimensions(dimensions)
        self.target = target
        self.alt = alt or target
        self.title = title

        self.align = alignment
        if self.align not in ('left', 'right', 'center'):
            self.align = None

    def build_node(self, context, format):
        ret_ = build_picture_node.send(sender=self,
                                       context=context,
                                       format=format)
        ret = filter(None, itertools.chain(
            map(operator.itemgetter(1), ret_)
        ))

        if ret:
            assert len(ret) == 1, "There must not be more than one node tree per context"
            return ret[0]

        #TODO: refactor using signals on rendering
        #      to get proper application independence
        if context.application == 'wiki':
            target = normalize_pagename(self.target, True)
        else:
            target = self.target

        wiki_page = context.kwargs.get('wiki_page', None)

        if wiki_page:
            target = join_pagename(wiki_page.name, target)

        source = fetch_real_target(target, width=self.width, height=self.height)

        img = nodes.Image(source, self.alt, class_='image-' +
                          (self.align or 'default'), title=self.title)
        if (self.width or self.height) and wiki_page is not None:
            return nodes.Link(fetch_real_target(target), [img])
        return img


class Date(Macro):
    """
    This macro accepts an `iso8601` string or unix timestamp (the latter in
    UTC) and formats it using the `format_datetime` function.
    """
    names = (u'Date', u'Datum')
    arguments = (
        ('date', unicode, None),
    )

    def __init__(self, date):
        if not date:
            self.now = True
        else:
            self.now = False
            try:
                self.date = parse_iso8601(date)
            except ValueError:
                try:
                    self.date = datetime.utcfromtimestamp(int(date))
                except ValueError:
                    self.date = None

    def build_node(self, context, format):
        if self.now:
            date = datetime.utcnow()
        else:
            date = self.date
        if date is None:
            return nodes.Text(_(u'Invalid date'))
        return nodes.Text(format_datetime(date))


class Newline(Macro):
    """
    This macro just forces a new line.
    """
    names = (u'BR',)
    is_static = True

    def build_node(self):
        return nodes.Newline()


class Anchor(Macro):
    """
    This macro creates an anchor accessible by url.
    """
    names = (u'Anchor', u'Anker')
    is_static = True
    arguments = (
        ('id', unicode, None),
    )

    def __init__(self, id):
        self.id = id

    def build_node(self):
        return nodes.Link(u'#%s' % self.id, id=self.id, class_='anchor',
                          children=[nodes.Text(u'')])


class Span(Macro):
    names = (u'SPAN',)
    is_static = True
    arguments = (
        ('content', unicode, ''),
        ('class_', unicode, None),
        ('style', unicode, None),
    )

    def __init__(self, content, class_, style):
        self.content = content
        self.class_ = class_
        self.style = filter_style(style) or None

    def build_node(self):
        return nodes.Span(children=[nodes.Text(self.content)],
                        class_=self.class_, style=self.style)


register(Anchor)
register(Newline)
register(Picture)
register(Date)
register(TableOfContents)
register(Span)