#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    inyoka.scripts.highlight_css
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The generate_highligh_css() function generates the css file for the
    ubuntuusers human highlighting style and writes it into the static
    directory.
    It's first argument should be a css expression for the element that
    contains the code to highlight.
    It should only be called manually.

    :copyright: (c) 2007-2012 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from os.path import join
from pygments.formatters import HtmlFormatter
from django.conf import settings
from inyoka.utils.highlight import HumanStyle


def generate_highlight_css(elm='.syntax'):
    formatter = HtmlFormatter(style=HumanStyle)
    path = join(settings.BASE_PATH, 'static/style/highlight.css')
    f = file(path, 'w+')
    f.write(formatter.get_style_defs(elm))
    f.close()


if __name__ == '__main__':
    generate_highlight_css()
