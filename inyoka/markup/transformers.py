# -*- coding: utf-8 -*-
"""
    inyoka.markup.transformers
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module holds ast transformers we use.  Transformers can assume that
    they always operate on complete trees, thus the outermost node is always
    a container node.

    Transformers are not necessarily the last thing that processes a tree.
    For example macros that are marked as tree processors and have have their
    stage attribute set to 'final' are expanded after all the transformers
    finished their job.

    :copyright: (c) 2007-2014 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import re

from django.utils.encoding import smart_unicode

from inyoka.markup import nodes

_newline_re = re.compile(r'(\n)')
_paragraph_re = re.compile(r'(\s*?\n){2,}')

#: A global cache for the smiley matching regular expression.
#: NOTE: This is unique for every process and never gets
#:       invalidated properly.  So theoretically every change
#:       on the smiley map requires an process restart.
#:       This is an awful hack but gives the wiki parser a massive speedup.
_smiley_re = None

def get_smiley_re(smilies):
    global _smiley_re
    if _smiley_re is None:
        helper = u'|'.join(re.escape(smart_unicode(s)) for s in
                           sorted(smilies, key=lambda x: -len(x)))
        regex = (u'(?<![\d\w])'  # don't precede smileys with alnum chars
                 u'({helper})'
                 u'(?![\d\w])'.format(helper=helper))
        _smiley_re = re.compile(regex, re.UNICODE)
    return _smiley_re


class Transformer(object):
    """
    Baseclass for all transformers.
    """

    def transform(self, tree):
        """
        This is passed a tree that should be processed.  A class can modify
        a tree in place, the return value has to be the tree then.  Otherwise
        it's safe to return a new tree.
        """
        return tree


class AutomaticParagraphs(Transformer):
    """
    This transformer is enabled per default and wraps elements in paragraphs.
    All macros and parsers depend on this parser so it's a terrible idea to
    disable this one.
    """

    def joined_text_iter(self, node):
        """
        This function joins multiple text nodes that follow each other into
        one.
        """
        text_buf = []

        def flush_text_buf():
            if text_buf:
                text = u''.join(text_buf)
                if text:
                    yield nodes.Text(text)
                del text_buf[:]

        for child in node.children:
            if child.is_text_node:
                text_buf.append(child.text)
            else:
                for item in flush_text_buf():
                    yield item
                yield child
        for item in flush_text_buf():
            yield item

    def transform(self, parent):
        """
        Insert real paragraphs into the node and return it.
        """
        for node in parent.children:
            if node.is_container and not node.is_raw:
                self.transform(node)

        if not parent.allows_paragraphs:
            return parent

        paragraphs = [[]]

        for child in self.joined_text_iter(parent):
            if child.is_text_node:
                blockiter = iter(_paragraph_re.split(child.text))
                for block in blockiter:
                    try:
                        is_paragraph = blockiter.next()
                    except StopIteration:
                        is_paragraph = False
                    if block:
                        paragraphs[-1].append(nodes.Text(block))
                    if is_paragraph:
                        paragraphs.append([])
            elif child.is_block_tag:
                paragraphs.extend((child, []))
            else:
                paragraphs[-1].append(child)

        del parent.children[:]
        for paragraph in paragraphs:
            if not isinstance(paragraph, list):
                parent.children.append(paragraph)
            else:
                for node in paragraph:
                    if not node.is_text_node or node.text:
                        parent.children.append(nodes.Paragraph(paragraph))
                        break

        return parent


class SmileyInjector(Transformer):
    """
    Adds smilies from the configuration.
    """

    def __init__(self, smiley_set=None):
        self.smiley_set = smiley_set

    def transform(self, tree):
        if self.smiley_set is not None:
            smilies = self.smiley_set
        else:
            from inyoka.wiki.storage import storage
            smilies = dict(storage.smilies)
        if not smilies:
            return tree

        smiley_re = get_smiley_re(smilies)

        new_children = []
        for node in tree.children:
            new_children.append(node)
            if node.is_container and not node.is_raw:
                self.transform(node)
            elif node.is_text_node and not node.is_raw:
                pos = 0
                text = node.text
                for match in smiley_re.finditer(text):
                    node.text = text[pos:match.start(1)]
                    if not node.text:
                        new_children.pop()
                    code = match.group(1)
                    pos = match.end(1)
                    node = nodes.Text()
                    new_children.extend((
                        nodes.Image(smilies[code], code),
                        node
                    ))
                if pos and text[pos:]:
                    node.text = text[pos:]
                if not node.text:
                    new_children.pop()
        tree.children[:] = new_children
        return tree


class KeyHandler(Transformer):
    """
    Removes unused paragraphs around key templates.
    """

    def transform(self, tree, nested=False):
        new_children = []
        for idx, node in enumerate(tree.children):
            contains_key = False
            is_special_container = type(node) in (nodes.Paragraph, nodes.Container)
            if hasattr(node, 'class_') and node.class_ == 'key':
                return tree, True
            if node.is_container and not node.is_raw and is_special_container:
                node, contains_key = self.transform(node, nested=True)
            if contains_key:
                new_children.extend(node.children)
            else:
                new_children.append(node)
        tree.children = new_children
        if nested:
            return tree, False
        return tree


class FootnoteSupport(Transformer):
    """
    Looks for footnote nodes, gives them an unique id and moves the
    text to the bottom into a list.  Without this translator footnotes
    are just <small>ed and don't have an id.
    """

    def transform(self, tree):
        footnotes = []
        for footnote in tree.query.by_type(nodes.Footnote):
            footnotes.append(footnote)
            footnote.id = len(footnotes)

        if footnotes:
            container = nodes.List('unordered', class_='footnotes')
            for footnote in footnotes:
                backlink = nodes.Link('#bfn-%d' % footnote.id,
                                      [nodes.Text(unicode(footnote.id))],
                                      id='fn-%d' % footnote.id)
                node = nodes.ListItem([backlink, nodes.Text(': ')] +
                                      footnote.children)
                container.children.append(node)
            tree.children.append(container)
        return tree


class HeadlineProcessor(Transformer):
    """
    This transformer looks at all headlines and makes sure that every ID is
    unique.  If one id clashes with another headline ID a numeric suffix is
    added.  What this transformer does not do is resolving clashes with
    footnotes or other references.  At least not by now because such clashes
    are very unlikely.
    """

    def transform(self, tree):
        id_map = {}
        for headline in tree.query.by_type(nodes.Headline):
            while True:
                if not headline.id:
                    headline.id = 'empty-headline'
                if headline.id not in id_map:
                    id_map[headline.id] = 1
                    break
                else:
                    id_map[headline.id] += 1
                    headline.id += '-%d' % id_map[headline.id]
        return tree


class AutomaticStructure(Transformer):
    """
    This transformer adds additional structure information.  Each headline
    adds either a new section or subsection depending on its level.
    """

    def transform(self, tree):
        if not tree.is_container:
            return tree
        struct = [[]]
        for node in tree.children:
            if isinstance(node, nodes.Headline):
                while node.level < len(struct):
                    struct.pop()
                while node.level > len(struct) - 1:
                    sec = nodes.Section(len(struct))
                    struct[-1].append(sec)
                    struct.append(sec.children)
            struct[-1].append(node)
        tree.children = struct[0]
        return tree


DEFAULT_TRANSFORMERS = [AutomaticParagraphs(),
                        SmileyInjector(), FootnoteSupport(),
                        HeadlineProcessor(), AutomaticStructure(),
                        KeyHandler()]
