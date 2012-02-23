#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    inyoka.scripts.wiki_excerpt
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The ``run`` method reads all wiki pages that are not listed in
    ``EXCLUDE_PAGES`` or its sub-pages. It checks that anonymous user has
    *read* permissions. It cleans the pages from ``Box`` and ``MetaData``
    nodes.  Afterwards all kind of whitespaces are replaced by a space.


    :copyright: (c) 2012 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import sys
import re
import csv

from itertools import izip

from inyoka.portal.user import User
from inyoka.utils.terminal import ProgressBar, percentize
from inyoka.wiki.acl import has_privilege
from inyoka.wiki.models import Page
from inyoka.wiki.parser.nodes import Box, Document, MetaData, Node


EXCLUDE_PAGES = [u'Benutzer/', u'Anwendertreffen/', u'Baustelle/',
                 u'LocoTeam/', u'Wiki/Vorlagen', u'Vorlage/', u'Verwaltung/',
                 u'Galerie', u'Trash/', u'Messen/', u'UWN-Team/',
                 u'Mitmachen/', u'ubuntuusers/']
EXCERPT_LENGTH = 200
USER = User.objects.get_anonymous_user()
WHITESPACE_REPLACE_RE = re.compile("\s+")


def clean(node):
    """
    Remove all ``Box`` and ``MetaData`` nodes from this node and all child
    nodes.
    """
    if hasattr(node, 'children'):
        for c in reversed(node.children):
            if isinstance(c, (Box, MetaData)):
                node.children.remove(c)
            else:
                clean(c)


def truncate(s, max_length):
    """
    Truncate the string ``s`` to a max length of ``max_length``. If ``s`` is
    empty, an empty string is returned.
    """
    width = min(len(s) - 1, max_length)
    if width > 0:
        if s[width].isspace():
            return s[0:width];
        return s[0:width].rsplit(None, 1)[0]
    return ""


def extract(pname, writer):
    """
    Extract the first ``EXCERPT_LENGTH`` characters from the the wiki page
    ``pname`` and write it to the csv writer ``writer``.
    """
    if not has_privilege(USER, pname, 'read'):
        return

    try:
        p = Page.objects.get_by_name(pname, nocache=False,
                raise_on_deleted=True)
    except Page.DoesNotExist:
        return

    doc = p.last_rev.text.parse()
    clean(doc)
    txt = doc.text.strip()
    out = WHITESPACE_REPLACE_RE.sub(u" ", txt)
    writer.writerow([p.name.encode('utf-8'), truncate(out, EXCERPT_LENGTH).encode('utf-8')])


def run():
    excerpt_writer = csv.writer(open('wiki-excerpt.csv', 'wb'), delimiter=';',
            quotechar='"', quoting=csv.QUOTE_ALL)

    unsorted = Page.objects.get_page_list(existing_only=True)
    pages = set()
    excluded_pages = set()
    # sort out excluded pages
    for page in unsorted:
        for exclude in EXCLUDE_PAGES:
            if exclude.lower() in page.lower():
                excluded_pages.add(page)
            else:
                pages.add(page)

    page_names = pages - excluded_pages

    pb = ProgressBar(40)
    percents = list(percentize(len(page_names)))
    for percent, pname in izip(percents, page_names):
        extract(pname, excerpt_writer)
        pb.update(percent)
    pb.update(100)
    print "Created excerpt on file "


if __name__ == '__main__':
    run()
