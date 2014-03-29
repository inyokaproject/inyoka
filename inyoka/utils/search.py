# -*- coding: utf-8 -*-

from haystack.utils.highlighting import Highlighter
from jinja2 import contextfilter


@contextfilter
def search_highlight(context, value):
    if 'query' in context:
        highlighter = Highlighter(context['query'])
        return highlighter.highlight(value)
    return value
