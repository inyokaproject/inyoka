# -*- coding: utf-8 -*-
"""
    inyoka.utils.highlight
    ~~~~~~~~~~~~~~~~~~~~~~

    This module summarizes various highlighting tasks. It implements:

     * code highlighting using `Pygments <http://pygments.org>`
     * Text excerpt highlighting used by the search system.

    The text excerpt highlighting system is borrowed from
    `Haystack-Xapian <https://github.com/notanumber/xapian-haystack>`
    but heavily modified to fix some bugs.

    :copyright: (c) 2007-2022 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import re
from itertools import chain

from django.utils.safestring import mark_safe
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import (
    TextLexer,
    get_lexer_by_name,
    get_lexer_for_filename,
    get_lexer_for_mimetype,
)
from pygments.util import ClassNotFound

from inyoka.utils.html import striptags

_pygments_formatter = HtmlFormatter(style='colorful',
                                    cssclass='notranslate syntax',
                                    linenos='table')

# split string into words, spaces, punctuation and markup tags
_split_re = re.compile(r'<\w+[^>]*>|</\w+>|[\w\']+|\s+|[^\w\'\s<>/]+')

# regular expression for the tested for box
_tested_for_re = re.compile(r'<div class="box tested_for">(.+?)</div>',
                            re.M | re.S)


def highlight_code(code, lang=None, filename=None, mimetype=None):
    """Highlight a block using pygments to HTML."""
    try:
        lexer = None
        guessers = [(lang, get_lexer_by_name),
            (filename, get_lexer_for_filename),
            (mimetype, get_lexer_for_mimetype)]
        for var, guesser in guessers:
            if var is not None:
                try:
                    lexer = guesser(var, stripnl=False, startinline=True)
                    break
                except ClassNotFound:
                    continue

        if lexer is None:
            lexer = TextLexer(stripnl=False)
    except LookupError:
        lexer = TextLexer(stripnl=False)
    return mark_safe(highlight(code, lexer, _pygments_formatter))


class Highlighter(object):
    css_class = 'highlight'
    html_tag = 'em'
    max_length = 200
    text_block = ''

    def __init__(self, query, **kwargs):
        self.query = query
        # ignore short words (since we actually search in the text and not
        # for whole words).
        self.query_words = set(word.lower()
                               for word in query.split()
                               if not word.startswith('-') and len(word) > 2)

    def highlight(self, text_block):
        self.text_block = striptags(text_block)
        highlight_locations = self.find_highlightable_words()
        start_offset, end_offset = self.find_window(highlight_locations)
        return self.render_html(highlight_locations, start_offset, end_offset)

    def find_highlightable_words(self):
        # Use a set so we only do this once per unique word.
        word_positions = {}

        # Pre-compute the length.
        end_offset = len(self.text_block)
        lower_text_block = self.text_block.lower()

        for word in self.query_words:
            if word not in word_positions:
                word_positions[word] = []

            start_offset = 0

            while start_offset < end_offset:
                next_offset = lower_text_block.find(word, start_offset,
                                                    end_offset)

                # If we get a -1 out of find, it wasn't found. Bomb out and
                # start the next word.
                if next_offset == -1:
                    break

                word_positions[word].append(next_offset)
                start_offset = next_offset + len(word)

        return word_positions

    def find_window(self, highlight_locations):
        best_start = 0
        best_end = self.max_length

        # First, make sure we have words.
        if not len(highlight_locations):
            return (best_start, best_end)

        # Next, make sure we found any words at all and sort them.
        words_found = sorted(chain(*list(highlight_locations.values())))

        if not len(words_found):
            return (best_start, best_end)

        if len(words_found) == 1:
            return (words_found[0], words_found[0] + self.max_length)

        # We now have a denormalized list of all positions were a word was
        # found. We'll iterate through and find the densest window we can by
        # counting the number of found offsets (-1 to fit in the window).
        highest_density = 0

        if words_found[-1] > self.max_length:
            best_start = words_found[-1]
            best_end = best_start + self.max_length

        start = 0
        end = 1
        max_length = self.max_length
        while start < len(words_found):
            start_pos = words_found[start]
            while end < len(words_found) and words_found[end] - start_pos < max_length:
                end += 1
            current_density = end - start
            # Only replace if we have a bigger (not equal density) so we
            # give deference to windows earlier in the document.
            if current_density > highest_density:
                best_start = start_pos
                best_end = start_pos + max_length
                highest_density = current_density
            start += 1

        return (best_start, best_end)

    def render_html(self, highlight_locations=None, start_offset=None,
                    end_offset=None):
        # Start by chopping the block down to the proper window.
        text = self.text_block[start_offset:end_offset]

        # Invert highlight_locations to a location -> term list
        term_list = []

        for term, locations in list(highlight_locations.items()):
            term_list += [(loc - start_offset, term) for loc in locations]

        loc_to_term = sorted(term_list)

        # Prepare the highlight template
        if self.css_class:
            hl_start = '<%s class="%s">' % (self.html_tag, self.css_class)
        else:
            hl_start = '<%s>' % (self.html_tag)

        hl_end = '</%s>' % self.html_tag

        # Copy the part from the start of the string to the first match,
        # and there replace the match with a highlighted version.
        highlighted_chunk = ""
        matched_so_far = 0
        prev = 0
        prev_str = ""

        for cur, cur_str in loc_to_term:
            # This can be in a different case than cur_str
            actual_term = text[cur:cur + len(cur_str)]

            # Handle incorrect highlight_locations by first looking for the term
            if actual_term.lower() == cur_str:
                highlighted_chunk += (text[prev + len(prev_str):cur] + hl_start
                                      + actual_term + hl_end)
                prev = cur
                prev_str = cur_str

                # Keep track of how far we've copied so far, for the last step
                matched_so_far = cur + len(actual_term)

        # Don't forget the chunk after the last term
        highlighted_chunk += text[matched_so_far:]

        if start_offset > 0:
            highlighted_chunk = '...%s' % highlighted_chunk

        if end_offset < len(self.text_block):
            highlighted_chunk = '%s...' % highlighted_chunk

        return highlighted_chunk


def create_excerpt(text, query):
    text = text.replace('<br />', ' ').replace('<p>', ' ')
    highlighter = Highlighter(query)
    return highlighter.highlight(text)
