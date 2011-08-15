# -*- coding: utf-8 -*-
"""
    inyoka.utils.highlight
    ~~~~~~~~~~~~~~~~~~~~~~

    This module summarizes various highlighting tasks. It implements:

     * code highlighting using `Pygments <http://pygments.org>`

    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import re
from pygments import highlight
from pygments.lexers import get_lexer_by_name, get_lexer_for_filename, \
    get_lexer_for_mimetype, TextLexer
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound
from pygments.styles.friendly import FriendlyStyle


_pygments_formatter = HtmlFormatter(style='colorful', cssclass='notranslate syntax',
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
    return highlight(code, lexer, _pygments_formatter)


class HumanStyle(FriendlyStyle):
    """
    This is a pygments style that matches the ubuntuusers design.
    """
