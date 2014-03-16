# -*- coding: utf-8 -*-
"""
    inyoka.utils.highlight
    ~~~~~~~~~~~~~~~~~~~~~~

    This module summarizes various highlighting tasks. It implements:

     * code highlighting using `Pygments <http://pygments.org>`

    :copyright: (c) 2007-2014 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import re
from itertools import chain

from django.utils.safestring import mark_safe

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import (TextLexer, get_lexer_by_name,
    get_lexer_for_mimetype, get_lexer_for_filename)
from pygments.styles.friendly import FriendlyStyle
from pygments.util import ClassNotFound

from inyoka.utils.html import striptags


_pygments_formatter = HtmlFormatter(style='colorful',
                                    cssclass='notranslate syntax',
                                    linenos='table')


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


class HumanStyle(FriendlyStyle):
    """
    This is a pygments style that matches the ubuntuusers design.
    """
