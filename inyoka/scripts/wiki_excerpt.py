#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    inyoka.scripts.wiki_excerpt
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The ``run`` method reads all wiki pages that are not listed in
    ``EXCLUDE_PAGES`` or its sub-pages. It checks that anonymous user has
    *read* permissions. Afterwards all kind of whitespaces are replaced by a
    space.


    :copyright: (c) 2012 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import sys
import os
import re
import csv

from itertools import izip

from django.conf import settings
from django.utils.text import Truncator

from inyoka.portal.user import User
from inyoka.utils.terminal import ProgressBar, percentize, show
from inyoka.wiki.acl import has_privilege
from inyoka.wiki.models import Page
from inyoka import markup
from inyoka.markup.macros import TableOfContents
from inyoka.markup.nodes import Box, Container, Error, Footnote, Headline, MetaData


DEFAULT_EXCERPT_FILE = 'wiki-excerpt.csv'
EXCERPT_LENGTH = 50
EXCLUDE_PAGES = [settings.WIKI_MAIN_PAGE, settings.WIKI_TEMPLATE_BASE,
    u'%s/' % settings.WIKI_USER_BASE, u'%s/' % settings.WIKI_USERPAGE_INFO,
    u'Anwendertreffen/', u'Baustelle/', u'Galerie/', u'LocoTeam/', u'Messen/',
    u'Trash/', u'ubuntuusers/', u'UWN-Team/', u'Verwaltung/', u'Vorlagen',
    u'Wiki/']
PRUNE_NODES = (Box, Container, Error, Footnote, Headline, MetaData, TableOfContents)
USER = User.objects.get_anonymous_user()
WHITESPACE_REPLACE_RE = re.compile("\s+")


def extract(pname, writer):
    """
    Extract the first ``EXCERPT_LENGTH`` words from the the wiki page
    ``pname`` and write it to the csv writer ``writer``.
    """
    if not has_privilege(USER, pname, 'read'):
        return

    try:
        p = Page.objects.get_by_name(pname, nocache=False,
                raise_on_deleted=True)
    except Page.DoesNotExist:
        return
    if p.last_rev.attachment:
        return
    doc = markup.parse(p.last_rev.text.value, drop_nodes=PRUNE_NODES)
    txt = doc.text.strip()
    out = WHITESPACE_REPLACE_RE.sub(u" ", txt)
    writer.writerow([p.name.encode('utf-8'),
                     p.get_absolute_url(action='show'),
                     Truncator(out).words(EXCERPT_LENGTH, truncate='').encode('utf-8')])


def run(output):
    excerpt_file = open(output, 'wb')
    excerpt_writer = csv.writer(excerpt_file, delimiter=';',
            quotechar='"', quoting=csv.QUOTE_ALL)

    unsorted = Page.objects.get_page_list(existing_only=True)
    pages = set()
    excluded_pages = set()
    # drop excluded pages
    exclude_pages = [x.lower() for x in EXCLUDE_PAGES]
    for page in unsorted:
        for exclude in exclude_pages:
            if page.lower().startswith(exclude):
                excluded_pages.add(page)
            else:
                pages.add(page)

    page_names = pages - excluded_pages

    if settings.DEBUG:
        print "Creating wiki excerpts to file '%s'" % \
            os.path.abspath(excerpt_file.name)
        pb = ProgressBar(40)
        percents = list(percentize(len(page_names)))
        for percent, pname in izip(percents, page_names):
            extract(pname, excerpt_writer)
            pb.update(percent)
        pb.update(100)
        show('\n')
    else:
        for pname in page_names:
            extract(pname, excerpt_writer)

    excerpt_file.close()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        run(sys.argv[1])
    else:
        run(DEFAULT_EXCERPT_FILE)
