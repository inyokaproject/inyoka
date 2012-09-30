# -*- coding: utf-8 -*-
"""
    inyoka.wiki.utils
    ~~~~~~~~~~~~~~~~~

    Contains various helper functions for the wiki.  Most of them are only used
    for the wiki application itself, but there are use cases for some of them
    outside of the wiki too.  Any example for that is the diff renderer which
    might be useful for the pastebin too.


    :copyright: (c) 2007-2012 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from django.utils.html import smart_urlquote

from inyoka.wiki.storage import storage
from inyoka.utils.urls import href


def has_conflicts(text):
    """Returns `True` if there are conflict markers in the text."""
    from inyoka.markup import parse, nodes
    if isinstance(text, basestring):
        text = parse(text)
    return text.query.all.by_type(nodes.ConflictMarker).has_any


def get_smilies(full=False):
    """
    This method returns a list of tuples for all the smilies in the storage.
    Per default for multiple codes only the first one is returend, if you want
    all codes set the full parameter to `True`.
    """
    if full:
        return storage.smilies[:]
    result = []
    images_yielded = set()
    for code, img in storage.smilies:
        if img in images_yielded:
            continue
        result.append((code, img))
        images_yielded.add(img)
    return result


def resolve_interwiki_link(wiki, page):
    """
    Resolve an interwiki link. If no such wiki exists the return value
    will be `None`.
    """
    if wiki == 'user':
        return href('portal', 'user', page)
    if wiki == 'attachment':
        return href('wiki', '_attachment', target=page)
    rule = storage.interwiki.get(wiki)
    if rule is None:
        return
    quoted_page = smart_urlquote(page)
    if '$PAGE' not in rule:
        link = rule + quoted_page
    else:
        link = rule.replace('$PAGE', quoted_page)
    return link


def quote_text(text, author=None, item_url=None):
    """
    Returns the wiki syntax quoted version of `text`.
    If the optional argument `author` (username as string or User object) is
    given, a written-by info is prepended.
    """
    try:  # We use try/catch here to not have to import the User model
        author = author.username
    except AttributeError:
        pass

    if item_url:
        by = author and (u'[user:%s:] [%s schrieb]:\n' % (author, item_url)) or u''
    else:
        by = author and (u"[user:%s:] schrieb:\n" % author) or u''
    return text and by + u'\n'.join(
        '>' + (not line.startswith('>') and ' ' or '') + line
        for line in text.split('\n')
    ) or u''
