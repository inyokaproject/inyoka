"""
inyoka.utils.html
~~~~~~~~~~~~~~~~~

This module implements various HTML utility functions.

:copyright: (c) 2007-2026 by the Inyoka Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from html.parser import HTMLParser
from xml.sax.saxutils import quoteattr

import nh3


def build_html_tag(tag, class_=None, classes=None, **attrs):
    """Build an HTML opening tag."""
    if classes:
        class_ = ' '.join(x for x in classes if x)
    if class_:
        attrs['class'] = class_

    attr_string = ' '.join(
        iter(
            '%s=%s' % (k, quoteattr(str(v))) for k, v in attrs.items() if v is not None
        )
    )

    return '<%s%s>' % (
        tag,
        attr_string and ' ' + attr_string or '',
    )


class AddParagraphs(HTMLParser):
    """Adds <p> to HTML, when a top-level text has no parent element."""

    inside_tag = False
    level = 0
    data = ''

    def handle_starttag(self, tag, attrs):
        self.inside_tag = True
        self.level += 1
        self.data += build_html_tag(tag, class_=None, classes=None, **dict(attrs))

    def handle_endtag(self, tag):
        self.inside_tag = False
        self.level -= 1
        self.data += f'</{tag}>'

    def handle_data(self, data):
        if self.inside_tag or self.level > 0:
            self.data += data
        elif data := data.strip():
            self.data += f'<p>{data}</p>'


def cleanup_html(html, nh3_cleaner: nh3.Cleaner) -> str:
    html = nh3_cleaner.clean(html)

    parser = AddParagraphs()
    parser.feed(html)
    return parser.data
