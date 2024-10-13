"""
    inyoka.utils.highlight
    ~~~~~~~~~~~~~~~~~~~~~~

    This module implements a reusable helper for code highlighting using `Pygments <http://pygments.org>`

    :copyright: (c) 2007-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
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
