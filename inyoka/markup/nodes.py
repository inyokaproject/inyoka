# -*- coding: utf-8 -*-
"""
    inyoka.markup.nodes
    ~~~~~~~~~~~~~~~~~~~

    The nodes for the parse tree of the parser.

    Nodes also provide the formatting methods to generate HTML or whatever.
    If you want to add new formatting methods don't forget to
    register it in the dispatching functions.  Also in the other modules
    and especially in macro and parser baseclasses.

    All nodes except of the base nodes have to have a `__dict__`.  This is
    enforced because dict-less objects cannot be replaced in place which is
    a required by the `DeferredNode`.


    :copyright: (c) 2007-2019 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from urlparse import urlparse, urlunparse

from django.conf import settings
from django.utils.html import escape
from django.utils.translation import ugettext_lazy, ugettext as _

from inyoka.markup.machine import NodeRenderer, NodeCompiler, NodeQueryInterface
from inyoka.markup.utils import debug_repr
from inyoka.utils.html import striptags, build_html_tag
from inyoka.utils.templating import render_template
from inyoka.utils.text import slugify, get_pagetitle, normalize_pagename
from inyoka.utils.urls import href, urlquote_plus


def error_box(title, message):
    """Create an error node."""
    return Error([
        Strong([Text(title)]),
        Paragraph([Text(message)])
    ])


def html_partial(template_name, block_level=False, **context):
    """
    Return a `HTMLOnly` node with the rendered template and an empty
    fallback for non HTML output.
    """
    rv = render_template(template_name, context)
    return HTMLOnly(rv, Node(), block_level=block_level)


class BaseNode(object):
    """
    internal Baseclass for all nodes.  Usually you inherit from `Node`
    that implements the renderer and compiler interface but sometimes
    it can be useful to have a plain node.
    """
    __slots__ = ()

    #: if the current node is a document node (outermost one) this is
    #: true. So far there is only one node which is called "document",
    #: in the future a node "Page" could be added that has layout information
    #: for printing.
    is_document = False

    #: if this node contains child nodes (has a children attribute)
    #: this is true. Also containers are usually subclasses of the
    #: `Container` node but that's not a requirement.
    is_container = False

    #: this is true if the element is a block tag. Block tags can contain
    #: paragraphs and inline elements. All containers that are not block
    #: tags are inline tags and can only contain inline tags.
    is_block_tag = False

    #: this is true if the element is a paragraph node
    is_paragraph = False

    #: this is true of this element can contain paragraphs.
    allows_paragraphs = False

    #: True if this is a text node
    is_text_node = False

    #: allowed in signatures?
    allowed_in_signatures = False

    #: This is true of the node contains raw data. Raw data is data that is
    #: never processed by a transformer. For example if you don't want
    #: to have typographical quotes this is the flag to alter. Use this only
    #: if the contents of that node matter (sourcecode etc.)
    is_raw = False

    #: the value of the node as text
    text = u''

    #: whether the node is just for creating line breaks
    is_linebreak_node = False

    def __eq__(self, other):
        return self.__class__ is other.__class__ and \
            self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self.__eq__(other)

    __repr__ = debug_repr


class DeferredNode(BaseNode):
    """
    Special node with a `become()` function that can be used to replace
    this node in place with another one.
    """

    def __init__(self, node):
        self.node = node

    @property
    def is_block_tag(self):
        return self.node.is_block_tag

    def become(self, other):
        self.__class__ = other.__class__
        self.__dict__ = other.__dict__


class Node(BaseNode, NodeRenderer, NodeCompiler, NodeQueryInterface):
    """
    The public baseclass for all nodes.  It implements the `NodeRenderer`
    and `NodeCompiler` and sets some basic attributes every node must have.
    """

    def prepare(self, format):
        """
        Public interface to the rendering functions.  This is only a
        dispatcher on the basenode, the preparation methods always
        *have* to call themselves with their internal name for
        performance reasons.  The `prepare()` method itself is only
        used by the renderer and node compiler.
        """
        return {
            'html': self.prepare_html
        }[format]()

    def prepare_html(self):
        """
        The AST itself never survives the parsing process.  At the end
        of parsing `prepare_html` is called and the iterator returned is
        converted into an active cacheable object (pickled if it contains
        dynamic rendering parts, otherwise dumped as utf-8 string).
        """
        return iter(())


class Text(Node):
    """
    Represents text.
    """

    is_text_node = True
    allowed_in_signatures = True

    def __init__(self, text=u''):
        self.text = text

    def prepare_html(self):
        yield escape(self.text)


class HTML(Node):
    """
    Raw HTML snippet.
    """

    allowed_in_signatures = True

    def __init__(self, html=u'', block_level=True):
        self.html = html
        self.is_block_tag = block_level

    @property
    def text(self):
        return striptags(self.html)

    def prepare_html(self):
        yield self.html


class HTMLOnly(HTML):
    """
    Like `HTML` but with a fallback for non HTML formats.
    """

    def __init__(self, html, fallback, block_level=True):
        HTML.__init__(self, html, block_level)
        self.fallback = fallback


class MetaData(Node):
    """
    Holds invisible metadata.  Never rendered.
    """

    is_block_tag = False
    allowed_in_signatures = True

    def __init__(self, key, values):
        self.key = key
        self.values = values


class Newline(Node):
    """
    A newline in a paragraph.  Never use multiple of those.
    """

    allowed_in_signatures = True
    is_linebreak_node = True

    @property
    def text(self):
        return '\n'

    def prepare_html(self):
        yield u'<br />'


class Ruler(Node):
    """
    Newline with line.
    """

    is_block_tag = True

    def prepare_html(self):
        yield u'<hr />'


class ConflictMarker(Node):
    """
    Represents a conflict marker in the markup.  The type argument must
    be one of `left`, `middle`, or `right`.
    """

    is_block_tag = True

    def __init__(self, type):
        self.type = type

    def prepare_html(self):
        yield u'<div class="conflict conflict-%s">' % self.type
        yield {
            'left': _(u'<strong>Conflict</strong> – remote version'),
            'middle': _(u'<strong>Conflict</strong> – local Version'),
            'right': _(u'<strong>Conflict End</strong>')
        }[self.type]
        yield u'</div>'


class Macro(Node):
    """
    Reference to a runtime macro.
    """

    def __init__(self, macro):
        self.macro = macro

        # if there is metadata in a dynamic macro we copy it
        # over to this node and mark the node as container node.
        if macro.metadata is not None:
            self.is_container = True
            self.children = macro.metadata
            macro.metadata = None

    @property
    def is_block_tag(self):
        return self.macro.is_block_tag

    def prepare_html(self):
        yield self.macro


class Parser(object):
    """
    Reference to a runtime parser.
    """

    def __init__(self, parser):
        self.parser = parser

    @property
    def text(self):
        return self.parser.data

    @property
    def is_block_tag(self):
        return self.parser.is_block_tag

    def prepare_html(self):
        yield self.parser


class Image(Node):
    """
    Holds a reference to an image.  Because images are quite problematic for
    alternative output formats it's supported to replace it with the alt tag
    on rendering.  So far images targets are always absolute urls.
    """

    def __init__(self, href, alt, id=None, class_=None, style=None, title=None):
        self.href = href
        self.alt = alt
        self.title = title
        self.id = id
        self.class_ = class_
        self.style = style

    def prepare_html(self):
        yield build_html_tag(u'img', src=self.href, alt=self.alt, id=self.id,
                             class_=self.class_, style=self.style,
                             title=self.title, loading='lazy')

    def __setstate__(self, dict):
        self.__dict__ = dict
        if 'title' not in dict:
            self.title = None


class Container(Node):
    """
    A basic node with children.
    """
    is_container = True

    #: this is true if the container is plain (unstyled)
    is_plain = True

    def __init__(self, children=None):
        if children is None:
            children = []
        self.children = children

    def get_fragment_nodes(self, inline_paragraph=False):
        """
        This function returns a tuple in the form ``(children, is_block)``.
        If the container holds exactly one unstyled paragraph the elements
        in that paragraph are used if `inline_paragraph` is set to `True`.

        The `is_block` item in the tuple is `True` if the children returned
        required a block tag as container.
        """
        if inline_paragraph:
            if len(self.children) == 1 and self.children[0].is_paragraph and \
               self.children[0].is_plain:
                return self.children[0].children, False
        is_block_tag = False
        for child in self.children:
            if child.is_block_tag:
                is_block_tag = True
                break
        return self.children, is_block_tag

    @property
    def is_block_tag(self):
        return self.get_fragment_nodes()[1]

    @property
    def text(self):
        return u''.join(x.text for x in self.children)

    def prepare_html(self):
        for child in self.children:
            for item in child.prepare_html():
                yield item


class Document(Container):
    """
    Outermost node.
    """
    allows_paragraphs = True
    is_document = True
    allowed_in_signatures = True


class Raw(Container):
    """
    A raw container.
    """
    is_raw = True


class Element(Container):
    """
    Baseclass for elements.
    """

    def __init__(self, children=None, id=None, style=None, class_=None):
        Container.__init__(self, children)
        self.id = id
        self.style = style
        self.class_ = class_

    @property
    def is_plain(self):
        return self.id is self.style is self.class_ is None

    @property
    def text(self):
        rv = Container.text.__get__(self)
        if self.is_block_tag:
            return rv + '\n'
        return rv


class Span(Element):
    """
    Inline general text element
    """

    allowed_in_signatures = True

    def __init__(self, children=None, id=None,
                 style=None, class_=None):
        Element.__init__(self, children, id, style, class_)

    def prepare_html(self):
        yield build_html_tag(u'span',
            id=self.id,
            style=self.style,
            class_=self.class_,
        )
        for item in Element.prepare_html(self):
            yield item
        yield u'</span>'


class InternalLink(Element):
    """
    Page to page links.
    """

    allowed_in_signatures = True

    def __init__(self, page, children=None, force_existing=False,
                 anchor=None, id=None, style=None, class_=None):
        page = normalize_pagename(page)
        if not children:
            title = get_pagetitle(page)
            if anchor:
                text = _(u'{title} (section “{anchor}”)').format(title=title, anchor=anchor)
            else:
                text = title
            children = [Text(text)]
        Element.__init__(self, children, id, style, class_)
        self.existing = force_existing
        self.page = page
        self.anchor = anchor

    def prepare_html(self):
        if not self.existing:
            from inyoka.wiki.models import Page
            self.existing = Page.objects.exists(self.page)
        url = href('wiki', self.page)
        if self.anchor:
            url += '#' + urlquote_plus(self.anchor)
        yield build_html_tag(u'a',
            href=url,
            id=self.id,
            style=self.style,
            classes=('internal', u'' if self.existing else u'missing', self.class_)
        )
        for item in Element.prepare_html(self):
            yield item
        yield u'</a>'


class InterWikiLink(Element):
    """
    Link to other wikis.
    """

    allowed_in_signatures = True

    def __init__(self, wiki, page, children=None, anchor=None,
                 id=None, style=None, class_=None):
        if not children:
            children = [Text(page)]
        Element.__init__(self, children, id, style, class_)
        self.wiki = wiki
        self.page = page
        self.anchor = anchor

    def prepare_html(self):
        # Circular imports
        from inyoka.wiki.utils import resolve_interwiki_link
        target = resolve_interwiki_link(self.wiki, self.page)
        if target is None:
            for item in Element.prepare_html(self):
                yield item
            return
        if self.anchor:
            target += '#' + self.anchor
        yield build_html_tag(u'a',
            href=target,
            id=self.id,
            style=self.style,
            classes=(u'interwiki', u'interwiki-' + self.wiki,
                     self.class_)
        )
        for item in Element.prepare_html(self):
            yield item
        yield u'</a>'


class Link(Element):
    """
    External or anchor links.
    """

    allowed_in_signatures = True

    def __init__(self, url, children=None, title=None, id=None,
                 style=None, class_=None, shorten=False):
        if not children:
            if shorten and len(url) > 50:
                children = [
                    Span([Text(url[:36])], class_='longlink_show'),
                    Span([Text(url[36:-14])], class_='longlink_collapse'),
                    Span([Text(url[-14:])]),
                ]
            else:
                text = url
                if text.startswith('mailto:'):
                    text = text[7:]
                children = [Text(text)]
            if title is None:
                title = url
        Element.__init__(self, children, id, style, class_)
        self.title = title
        self.scheme = self.netloc = None
        if url is not None:
            try:
                self.scheme, self.netloc, self.path, self.params, self.querystring, \
                    self.anchor = urlparse(url)
                self.valid_url = True
            except ValueError:
                self.valid_url = False
        else:
            self.valid_url = False

    @property
    def href(self):
        if not self.valid_url:
            return 'invalid-url'
        else:
            return urlunparse((self.scheme, self.netloc, self.path, self.params,
                               self.querystring, self.anchor))

    def prepare_html(self):
        if self.scheme == 'javascript':
            yield escape(self.caption)
            return
        rel = None
        if not self.netloc or self.netloc == settings.BASE_DOMAIN_NAME or \
           self.netloc.endswith('.' + settings.BASE_DOMAIN_NAME):
            class_ = 'crosslink'
        else:
            class_ = 'external'
            rel = 'nofollow'

        yield build_html_tag(u'a',
            rel=rel,
            id=self.id,
            style=self.style,
            title=self.title,
            classes=(class_, self.class_),
            href=self.href
        )
        for item in Element.prepare_html(self):
            yield item
        yield u'</a>'


class Section(Element):

    def __init__(self, level, children=None, id=None, style=None, class_=None):
        Element.__init__(self, children, id, style, class_)
        self.level = level

    def __str__(self):
        return 'Section(%d)' % self.level

    def prepare_html(self):
        class_ = 'section_%d' % self.level
        if self.class_:
            class_ += ' ' + self.class_
        yield build_html_tag(u'section', id=self.id, style=self.style,
                             class_=class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</section>'


class Paragraph(Element):
    """
    A paragraph.  Everything is in there :-)
    (except of block level stuff)
    """
    is_block_tag = True
    is_paragraph = True
    allowed_in_signatures = True
    is_linebreak_node = True

    @property
    def text(self):
        return Element.text.__get__(self).strip() + '\n\n'

    def prepare_html(self):
        yield build_html_tag(u'p', id=self.id, style=self.style,
                             class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</p>'


class Error(Element):
    """
    If a macro is not renderable or not found this is
    shown instead.
    """
    is_block_tag = True
    allows_paragraphs = True

    def prepare_html(self):
        yield build_html_tag(u'div',
            id=self.id,
            style=self.style,
            classes=('error', self.class_)
        )
        for item in Element.prepare_html(self):
            yield item
        yield u'</div>'


class Footnote(Element):
    """
    This represents a footnote.  A transformer moves the actual
    text down to the bottom and sets an automatically incremented id.
    If that transformer is not activated a <small> section is rendered.
    """

    def prepare_html(self):
        if self.id is None:
            yield build_html_tag(u'small',
                id=self.id,
                style=self.style,
                classes=('note', self.class_)
            )
            for item in Element.prepare_html(self):
                yield item
            yield u'</small>'
        else:
            yield u'<a href="#fn-%d" id="bfn-%d" class="footnote">' \
                  u'<span class="paren">[</span>%d<span class="paren">]' \
                  u'</span></a>' % (self.id, self.id, self.id)


class Quote(Element):
    """
    A blockquote.
    """
    is_block_tag = True
    allows_paragraphs = True
    allowed_in_signatures = True

    def prepare_html(self):
        yield build_html_tag(u'blockquote', id=self.id, style=self.style,
                             class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</blockquote>'


class Edited(Element):
    """
    Text that describes an edit action.
    """
    is_block_tag = True
    allows_paragraphs = True
    allowed_in_signatures = False

    #: Title message for the edited box
    msg = ugettext_lazy(u'Edited by')

    #: CSS Class used for styling
    css_class = 'edited'

    def __init__(self, username, children=None, id=None, style=None,
                 class_=None):
        Element.__init__(self, children, id, style, class_)
        self.username = username

    def prepare_html(self):
        yield u'<div class="%s">' % self.css_class
        yield u'<p><strong>%s <a class="crosslink user" href="%s">' \
              u'%s</a>:</strong></p> ' % (self.msg,
                href('portal', 'user', self.username),
                  self.username)
        for item in Element.prepare_html(self):
            yield item
        yield u'</div>'


class Moderated(Edited):
    """
    Text that describes a moderation action.
    """
    msg = ugettext_lazy(u'Moderated by')
    css_class = 'moderated'


class Preformatted(Element):
    """
    Preformatted text.
    """
    is_block_tag = True
    is_raw = True
    allowed_in_signatures = True

    def prepare_html(self):
        yield build_html_tag(u'pre', id=self.id, style=self.style,
                             class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</pre>'


class Headline(Element):
    """
    Represents all kinds of headline tags.
    """
    is_block_tag = True

    def __init__(self, level, children=None, id=None, style=None, class_=None):
        Element.__init__(self, children, id, style, class_)
        self.level = level
        if id is None:
            self.id = slugify(self.text, convert_lowercase=False)

    def prepare_html(self):
        yield build_html_tag(u'h%d' % (self.level + 1),
            id=self.id,
            style=self.style,
            class_=self.class_
        )
        for item in Element.prepare_html(self):
            yield item
        yield u'<a href="#%s" class="headerlink">¶</a>' % self.id
        yield u'</h%d>' % (self.level + 1)


class Strong(Element):
    """
    Holds children that are emphasized strongly.  For HTML this will
    return a <strong> tag which is usually bold.
    """

    allowed_in_signatures = True

    def prepare_html(self):
        yield build_html_tag(u'strong', id=self.id, style=self.style,
                             class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</strong>'


class Highlighted(Strong):
    """
    Marks highlighted text.
    """

    def prepare_html(self):
        classes = ['highlighted']
        if self.class_:
            classes.append(self._class)
        yield build_html_tag(u'strong', id=self.id, style=self.style,
                             classes=classes)
        for item in Element.prepare_html(self):
            yield item
        yield u'</strong>'


class Emphasized(Element):
    """
    Like `Strong`, but with slightly less importance.  Usually rendered
    with an italic font face.
    """

    allowed_in_signatures = True

    def prepare_html(self):
        yield build_html_tag(u'em', id=self.id, style=self.style,
                             class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</em>'


class SourceLink(Element):

    allowed_in_signatures = False

    def __init__(self, target, children=None, id=None, style=None, class_=None):
        if children is None:
            children = [Text('[%d]' % target)]
        Element.__init__(self, children, id, style, class_)
        self.target = target

    @property
    def text(self):
        return '[%d]' % self.target

    def prepare_html(self):
        yield build_html_tag(u'sup', id=self.id, style=self.style,
                             class_=self.class_)
        yield u'<a href="#source-%d">' % self.target
        for item in Element.prepare_html(self):
            yield item
        yield u'</a></sup>'


class Code(Element):
    """
    This represents code. Usually formatted in a monospaced font that
    preserves whitespace. Additionally this node is maked raw so children
    are not touched by the altering translators.
    """
    is_raw = True
    allowed_in_signatures = True

    def prepare_html(self):
        yield build_html_tag(u'code', id=self.id, style=self.style,
                             class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</code>'


class Underline(Element):
    """
    This element exists for backwards compatibility to MoinMoin and should
    not be used.  It generates a span tag with an "underline" class for
    HTML.  It's also allowed to not render this element in a special way.
    """

    allowed_in_signatures = True

    def prepare_html(self):
        yield build_html_tag(u'span',
            id=self.id,
            style=self.style,
            classes=('underline', self.class_)
        )
        for item in Element.prepare_html(self):
            yield item
        yield u'</span>'


class Stroke(Element):
    """
    This element marks deleted text.
    """

    allowed_in_signatures = True

    def prepare_html(self):
        yield build_html_tag(u'del', id=self.id, style=self.style,
                             class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</del>'


class Small(Element):
    """
    This elements marks not so important text, so it removes importance.
    It's usually rendered in a smaller font.
    """

    allowed_in_signatures = True

    def prepare_html(self):
        yield build_html_tag(u'small', id=self.id, style=self.style,
                             class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</small>'


class Big(Element):
    """
    The opposite of Small, but it doesn't give the element a real emphasis.
    """

    allowed_in_signatures = True

    def prepare_html(self):
        yield build_html_tag(u'big', id=self.id, style=self.style,
                             class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</big>'


class Sub(Element):
    """
    Marks text as subscript.
    """

    allowed_in_signatures = True

    def prepare_html(self):
        yield build_html_tag(u'sub', id=self.id, style=self.style,
                             class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</sub>'


class Sup(Element):
    """
    Marks text as superscript.
    """

    allowed_in_signatures = True

    def prepare_html(self):
        yield build_html_tag(u'sup', id=self.id, style=self.style,
                             class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</sup>'


class Color(Element):
    """
    Gives the embedded text a color.  Like `Underline` it just exists because
    of backwards compatibility (this time to phpBB).
    """

    allowed_in_signatures = True

    def __init__(self, value, children=None, id=None, style=None,
                 class_=None):
        Element.__init__(self, children, id, style, class_)
        self.value = value

    def prepare_html(self):
        style = self.style and self.style + '; ' or ''
        style += 'color: %s' % self.value
        yield build_html_tag(u'span',
            id=self.id,
            style=style,
            class_=self.class_
        )
        for item in Element.prepare_html(self):
            yield item
        yield u'</span>'


class Size(Element):
    """
    Gives the embedded text a size.  Like `Underline` it just exists because
    of backwards compatibility.  Requires the font size in percent.
    """

    def __init__(self, size, children=None, id=None, style=None,
                 class_=None):
        Element.__init__(self, children, id, style, class_)
        self.size = size

    def prepare_html(self):
        style = self.style and self.style + '; ' or ''
        style += 'font-size: %.2f%%' % self.size
        yield build_html_tag(u'span',
            id=self.id,
            style=style,
            class_=self.class_
        )
        for item in Element.prepare_html(self):
            yield item
        yield u'</span>'


class Font(Element):
    """
    Gives the embedded text a font face.  Like `Underline` it just exists
    because of backwards compatibility.
    """

    allowed_in_signatures = True

    def __init__(self, faces, children=None, id=None, style=None,
                 class_=None):
        Element.__init__(self, children, id, style, class_)
        self.faces = faces

    def prepare_html(self):
        style = self.style and self.style + '; ' or ''
        style += "font-family: %s" % ', '.join(
            x in ('serif', 'sans-serif', 'fantasy') and x or "'%s'" % x
            for x in self.faces
        )
        yield build_html_tag(u'span',
            id=self.id,
            style=style,
            class_=self.class_
        )
        for item in Element.prepare_html(self):
            yield item
        yield u'</span>'


class DefinitionList(Element):
    """
    A list of defintion terms.
    """
    is_block_tag = True

    def prepare_html(self):
        yield build_html_tag(u'dl', id=self.id, style=self.style,
                             class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</dl>'


class DefinitionTerm(Element):
    """
    A definition term has a term (surprise) and a value (the children).
    """
    is_block_tag = True
    allows_paragraphs = True

    def __init__(self, term, children=None, id=None, style=None,
                 class_=None):
        Element.__init__(self, children, id, style, class_)
        self.term = term

    def prepare_html(self):
        yield build_html_tag(u'dt', class_=self.class_, style=self.style,
                             id=self.id)
        yield escape(self.term)
        yield u'</dt>'
        yield build_html_tag(u'dd', class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</dd>'


class List(Element):
    """
    Sourrounds list items so that they appear as list.  Make sure that the
    children are list items.
    """
    is_block_tag = True

    def __init__(self, type, children=None, id=None, style=None, class_=None):
        Element.__init__(self, children, id, style, class_)
        self.type = type

    def prepare_html(self):
        if self.type == 'unordered':
            tag = u'ul'
            cls = None
        else:
            tag = u'ol'
            cls = self.type
        yield build_html_tag(tag, id=self.id, style=self.style,
                             classes=(self.class_, cls))
        for item in Element.prepare_html(self):
            yield item
        yield u'</%s>' % tag


class ListItem(Element):
    """
    Marks the children as list item.  Use in conjunction with list.
    """
    is_block_tag = True
    allows_paragraphs = True

    def prepare_html(self):
        yield build_html_tag(u'li', id=self.id, style=self.style,
                             class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</li>'


class Box(Element):
    """
    A dialog like object.  Usually renders to a layer with one headline and
    a second layer for the contents.
    """
    is_block_tag = True
    allows_paragraphs = True

    def __init__(self, title=None, children=None, align=None, valign=None,
                 id=None, style=None, class_=None):
        Element.__init__(self, children, id, style, class_)
        self.title = title
        self.class_ = class_
        self.align = align
        self.valign = valign

    def prepare_html(self):
        style = []
        if self.align:
            style.append(u'text-align: ' + self.align)
        if self.valign:
            style.append(u'vertical-align: ' + self.valign)
        if self.style:
            style.append(self.style)
        yield build_html_tag(u'div',
            id=self.id,
            style=style and u' '.join(style) or None,
            classes=(self.class_,)
        )
        if self.title is not None:
            yield build_html_tag(u'h3', class_=self.class_)
            yield escape(self.title)
            yield u'</h3>'
        yield build_html_tag(u'div', classes=(u'contents',))
        for item in Element.prepare_html(self):
            yield item
        yield u'</div></div>'


class Layer(Element):
    """
    Like a box but without headline and an nested content section.  Translates
    into a plain old HTML div or something comparable.
    """
    is_block_tag = True
    allows_paragraphs = True

    def prepare_html(self):
        yield build_html_tag(u'div', id=self.id, style=self.style,
                             class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</div>'


class Table(Element):
    """
    A simple table.  This can only contain table rows.
    """
    is_block_tag = True

    def __init__(self, children=None, id=None, style=None, class_=None):
        Element.__init__(self, children, id, style, class_)

    def prepare_html(self):
        yield build_html_tag(u'table', id=self.id, class_=self.class_,
                             style=self.style)
        for item in Element.prepare_html(self):
            yield item
        yield u'</table>'


class TableRow(Element):
    """
    A row in a table.  Only contained in a table and the only children
    nodes supported are table cells and headers.
    """
    is_block_tag = True

    def __init__(self, children=None, id=None, style=None, class_=None):
        Element.__init__(self, children, id, style, class_)

    def prepare_html(self):
        yield build_html_tag(u'tr', id=self.id, class_=self.class_,
                             style=self.style)
        for item in Element.prepare_html(self):
            yield item
        yield u'</tr>'


class TableCell(Element):
    """
    Only contained in a table row and renders to a table cell.
    """
    is_block_tag = True
    _html_tag = 'td'

    def __init__(self, children=None, colspan=None, rowspan=None, align=None,
                 valign=None, id=None, style=None, class_=None):
        Element.__init__(self, children, id, style, class_)
        self.colspan = colspan or 0
        self.rowspan = rowspan or 0
        self.align = align
        self.valign = valign

    def prepare_html(self):
        style = []
        if self.align:
            style.append(u'text-align: ' + self.align)
        if self.valign:
            style.append(u'vertical-align: ' + self.valign)
        if self.style:
            style.append(self.style)

        yield build_html_tag(self._html_tag,
            colspan=self.colspan or None,
            rowspan=self.rowspan or None,
            style=style and u'; '.join(style) or None,
            id=self.id,
            class_=self.class_
        )

        for item in Element.prepare_html(self):
            yield item
        yield u'</%s>' % self._html_tag


class TableHeader(TableCell):
    """
    Exactly like a table cell but renders to <th>
    """
    _html_tag = 'th'
