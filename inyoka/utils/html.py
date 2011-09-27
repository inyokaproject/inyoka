# -*- coding: utf-8 -*-
"""
    inyoka.utils.html
    ~~~~~~~~~~~~~~~~~

    This module implements various HTML/XHTML utility functions.  Some parts
    of this module require the lxml and html5lib libraries.

    **TODO**: switch to lxml.etree for the internal tree representation once
    the bug with ``<DOCUMENT_ROOT>`` is fixed.


    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from __future__ import division
import re
from markupsafe import escape
from htmlentitydefs import name2codepoint
from xml.sax.saxutils import quoteattr
from html5lib import HTMLParser, treewalkers, treebuilders
from html5lib.serializer import XHTMLSerializer, HTMLSerializer
from html5lib.filters.optionaltags import Filter as OptionalTagsFilter
from html5lib.filters import sanitizer


#: set of tags that don't want child elements.
EMPTY_TAGS = set(['br', 'img', 'area', 'hr', 'param', 'meta', 'link', 'base',
                  'input', 'embed', 'col', 'frame', 'spacer'])

_entity_re = re.compile(r'&([^;]+);')
_strip_re = re.compile(r'<!--.*?-->|<[^>]*>(?s)')


#: a dict of html entities to codepoints. This includes the problematic
#: &apos; character.
html_entities = name2codepoint.copy()
html_entities['apos'] = 39
del name2codepoint


def _build_html_tag(tag, attrs):
    """Build an HTML opening tag."""
    attrs = u' '.join(iter(
        u'%s=%s' % (k, quoteattr(unicode(v)))
        for k, v in attrs.iteritems()
        if v is not None))

    return u'<%s%s%s>' % (
        tag, attrs and ' ' + attrs or '',
        tag in EMPTY_TAGS and ' /' or '',
    ), tag not in EMPTY_TAGS and u'</%s>' % tag or u''


def build_html_tag(tag, class_=None, classes=None, **attrs):
    """Build an HTML opening tag."""
    if classes:
        class_ = u' '.join(x for x in classes if x)
    if class_:
        attrs['class'] = class_
    return _build_html_tag(tag, attrs)[0]


def color_fade(c1, c2, percent):
    """Fades two html colors"""
    new_color = []
    for i in xrange(3):
        part1 = int(c1[i * 2:i * 2 + 2], 16)
        part2 = int(c2[i * 2:i * 2 + 2], 16)
        diff = part1 - part2
        new = int(part2 + diff * percent / 100)
        new_color.append(hex(new)[2:])
    return ''.join(new_color)


def _handle_match(match):
    name = match.group(1)
    if name in html_entities:
        return unichr(html_entities[name])
    if name[:2] in ('#x', '#X'):
        try:
            return unichr(int(name[2:], 16))
        except ValueError:
            return u''
    elif name.startswith('#'):
        try:
            return unichr(int(name[1:]))
        except ValueError:
            return u''
    return u''


def replace_entities(string):
    """
    Replace HTML entities in a string:

    >>> replace_entities('foo &amp; bar &raquo; foo')
    u'foo & bar \\xbb foo'
    """
    if string is None:
        return u''
    return _entity_re.sub(_handle_match, string)


def striptags(string):
    """Remove HTML tags from a string."""
    if string is None:
        return u''
    if isinstance(string, str):
        string = string.decode('utf8')
    return u' '.join(_strip_re.sub('', replace_entities(string)).split())


def parse_html(string, fragment=True):
    """
    Parse a tagsoup into a tree.  Currently this tree is a html5lib simpletree
    because of a bug in lxml2 or html5lib.  We will switch to etree sooner or
    later so do not use this function until this is solved.  For cleaning up
    markup you can use the `cleanup_html` function.
    """
    parser = HTMLParser(tree=treebuilders.getTreeBuilder('simpletree'))
    return (fragment and parser.parseFragment or parser.parse)(string)


def cleanup_html(string, sanitize=True, fragment=True, stream=False,
                 filter_optional_tags=False, id_prefix=None,
                 update_anchor_links=True, output_format='xhtml'):
    """Clean up some html and convert it to HTML/XHTML."""
    if not string.strip():
        return u''
    tree = parse_html(string, fragment)
    walker = treewalkers.getTreeWalker('simpletree')(tree)
    walker = CleanupFilter(walker, id_prefix, update_anchor_links)
    if filter_optional_tags:
        walker = OptionalTagsFilter(walker)
    if sanitize:
        walker = SanitizerFilter(walker)
    serializer = {
        'html':         HTMLSerializer,
        'xhtml':        XHTMLSerializer
    }[output_format]()
    rv = serializer.serialize(walker)
    if stream:
        return rv
    return u''.join(rv)


class SanitizerFilter(sanitizer.Filter):
    """
    Nonstandard sanitizer filter that strips <script> tags instead of escaping
    them.  While this is against the what-wg proposal it makes more sense for
    aggregated blog contents which tend to use reddit/digg buttons we don't
    want to have in escaped form.

    We also disallow <style> *blocks* here because they are not valid in non
    head sections.
    """

    def __iter__(self):
        sourceiter = iter(self.source)
        for t in sourceiter:
            if t['type'] == 'StartTag' and t['name'] in ('script', 'style'):
                needle = t['name']
                for t2 in sourceiter:
                    if t2['type'] == 'EndTag' and t2['name'] == needle:
                        break
                continue
            token = self.sanitize_token(t)
            if token:
                yield token


class CleanupFilter(object):
    """
    A simple filter that replaces XHTML deprecated elements with others.
    """

    tag_conversions = {
        'center':       ('span', 'text-align: center'),
        'u':            ('span', 'text-decoration: underline'),
        'menu':         ('ul', None),
        'strike':       ('del', None)
    }

    end_tags = dict((k, v[0]) for k, v in tag_conversions.iteritems())
    end_tags['font'] = 'span'

    def __init__(self, source, id_prefix=None, update_anchor_links=False):
        self.source = source
        self.id_prefix = id_prefix
        self.update_anchor_links = update_anchor_links

    def __iter__(self):
        id_map = {}
        deferred_links = {}
        stream = self.walk(id_map, deferred_links)

        if not self.update_anchor_links:
            result = stream
        else:
            result = list(stream)
            for target_id, link in deferred_links.iteritems():
                if target_id in id_map:
                    for idx, (key, value) in enumerate(link['data']):
                        if key == 'href':
                            link['data'][idx] = [key, '#' + id_map[target_id]]
                            break
        for item in result:
            yield item

    def walk(self, id_map, deferred_links):
        tracked_ids = set()

        for token in self.source:
            if token['type'] == 'StartTag':
                attrs = dict(reversed(token.get('data', ())))
                if token['name'] in self.tag_conversions:
                    new_tag, new_style = self.tag_conversions[token['name']]
                    token['name'] = new_tag
                    if new_style:
                        style = attrs.get('style') or ''
                        # this could give false positives, but the chance is
                        # quite small that this happens.
                        if new_style not in style:
                            attrs['style'] = (style and style.rstrip(';') +
                                              '; ' or '') + new_style + ';'

                elif token['name'] == 'a' and \
                     attrs.get('href', '').startswith('#'):
                    attrs.pop('target', None)
                    deferred_links[attrs['href'][1:]] = token

                elif token['name'] == 'font':
                    token['name'] = 'span'
                    attrs = dict(reversed(token.get('data', ())))
                    styles = []
                    tmp = attrs.pop('color', None)
                    if tmp:
                        styles.append('color: %s' % tmp)
                    tmp = attrs.pop('face', None)
                    if tmp:
                        styles.append('font-family: %s' % tmp)
                    tmp = attrs.pop('size', None)
                    if tmp:
                        styles.append('font-size: %s' % {
                            '1':    'xx-small',
                            '2':    'small',
                            '3':    'medium',
                            '4':    'large',
                            '5':    'x-large',
                            '6':    'xx-large'
                        }.get(tmp, 'medium'))
                    if styles:
                        style = attrs.get('style')
                        attrs['style'] = (style and style.rstrip(';') + ' ;'
                                          or '') + '; '.join(styles) + ';'

                elif token['name'] == 'img':
                    attrs.pop('border', None)
                    if 'alt' not in attrs:
                        attrs['alt'] = ''

                if 'id' in attrs:
                    element_id = original_id = attrs['id']
                    while element_id in tracked_ids:
                        element_id = increment_string(element_id)
                    tracked_ids.add(element_id)
                    if self.id_prefix:
                        element_id = self.id_prefix + element_id
                    attrs['id'] = element_id
                    id_map[original_id] = element_id
                token['data'] = [list(item) for item in attrs.items()]
            elif token['type'] == 'EndTag' and \
                 token['name'] in self.end_tags:
                token['name'] = self.end_tags[token['name']]
            yield token

# circ import
from inyoka.utils.text import increment_string
