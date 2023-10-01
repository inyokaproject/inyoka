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

    :copyright: (c) 2007-2023 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import re

from django.conf import settings
from django.utils.encoding import smart_str
from django.utils.functional import cached_property

from inyoka.markup import nodes

_newline_re = re.compile(r'(\n)')
_paragraph_re = re.compile(r'(\s*?\n){2,}')


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
                text = ''.join(text_buf)
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
                        is_paragraph = next(blockiter)
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
    smilies = settings.SMILIES

    def transform(self, tree):
        new_children = []
        for node in tree.children:
            new_children.append(node)
            if node.is_container and not node.is_raw:
                self.transform(node)
            elif node.is_text_node and not node.is_raw:
                pos = 0
                text = node.text

                for match in self.smiley_re.finditer(text):
                    new_node = self._new_smiley_node(match)

                    node.text = text[pos:match.start(1)]
                    if not node.text:
                        new_children.pop()
                    pos = match.end(1)
                    node = nodes.Text()
                    new_children.extend((
                        new_node,
                        node
                    ))
                if pos and text[pos:]:
                    node.text = text[pos:]
                if not node.text:
                    new_children.pop()
        tree.children[:] = new_children
        return tree

    def _convert_to_regional_indicator(self, country_code):
        """
        A two char ASCII string (`country_code`) will be converted to
        two regional indicator symbols. Most browsers will display
        these regional indicators as flags.
        See https://en.wikipedia.org/wiki/Regional_Indicator_Symbol
        """
        country_code = str.lower(country_code)

        # reproduces the legacy behaviour, that {en} displayed the british flag
        if country_code == 'en':
            country_code = 'gb'

        def to_regional_indicator(char):
            return chr(ord(char) - ord('a') + ord('🇦'))

        return ''.join(to_regional_indicator(char) for char in country_code)

    def _new_smiley_node(self, match):
        if match.group('country_code'):
            text = match.group('country_code')
            text = self._convert_to_regional_indicator(text)
        else:
            text = self.smilies[match.group(1)]

        keyword = 'css-class:'
        if text.startswith(keyword):
            return nodes.Span(class_=text[len(keyword):])

        return nodes.Text(text)

    @cached_property
    def smiley_re(self):
        """
        As DEFAULT_TRANSFORMERS instances this class and it's passed around,
        this property will be cached until the python process dies.
        """
        helper = '|'.join(re.escape(smart_str(s)) for s in self.smilies)
        helper += '|\{(?P<country_code>[a-z]{2}|[A-Z]{2})\}'
        regex = (
            '(?<![\d\w])'  # don't precede smileys with alnum chars
            '({helper})'
            '(?![\d\w])'.format(helper=helper))
        return re.compile(regex, re.UNICODE)


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
                                      [nodes.Text(str(footnote.id))],
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
