#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    inyoka.scripts.generate_snapshot
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Creates a snapshot of all wiki pages using docbook format.

    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import os
import re
import shutil
import urllib2
from os import path
from datetime import datetime
from itertools import izip

from inyoka.utils.urls import href
from inyoka.utils.text import normalize_pagename
from inyoka.wiki.models import Page
from inyoka.utils.templating import jinja_env
from inyoka.utils.terminal import percentize, ProgressBar


NESTED1 = re.compile('<ulink url="([^"]*)"><mediaobject><imageobject><imagedata')
NESTED2 = re.compile('/></imageobject></mediaobject></ulink>')
ABSOLUTE_LINK_REGEX = re.compile('<ulink url="/([^"]*)">')
INTERNAL_IMG_REGEX = re.compile('<imagedata fileref="%s\?target=([^"]*)' %
                                href('wiki', '_image'))
THUMBNAIL_REGEX = re.compile('<imagedata fileref="%s\?([^"]*)"' %
                             href('wiki', '_image'))


EXCLUDE_PAGES = [u'Benutzer/', u'Anwendertreffen/', u'Baustelle/', u'LocoTeam/',
                 u'Wiki/Vorlagen', u'Vorlage/', u'Verwaltung/', u'Galerie', 'Trash/',
                 u'Messen/', u'UWN-Team/', u'Startseite', u'intern']
# we're case insensitive
EXCLUDE_PAGES = [x.lower() for x in EXCLUDE_PAGES]


def handle_thumbnail(m):
    d = {}
    for s in m.groups()[0].split('&'):
        k, v = s.split('=')
        d[k] = v
    r = u'<imagedata fileref="./attachments/%s"' % urllib2.unquote(d['target'])
    if 'width' in d:
        r += u' width="%s"' % d['width']
    if 'height' in d:
        r += u' height="%s"' % d['height']
    return r


def handle_link(m):
    return u'<ulink url="./%s.xml">' % fix_path(m.groups()[0])


def fix_path(pth):
    if isinstance(pth, unicode):
        pth.encode('utf-8')
    return normalize_pagename(pth, False).lower()


def create_snapshot(folder):
    # remove the snapshot folder and recreate it
    try:
        shutil.rmtree(folder)
    except OSError:
        pass
    os.mkdir(folder)

    # create the snapshot folder structure
    page_folder = path.join(folder, 'pages')
    attachment_folder = path.join(folder, 'pages', 'attachments')
    os.mkdir(page_folder)
    os.mkdir(attachment_folder)

    tpl = jinja_env.get_template('snapshot/docbook_page.xml')

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
    todo = pages - excluded_pages
    percents = list(percentize(len(todo)))
    pb = ProgressBar(40)

    processed = set()

    for percent, name in izip(percents, todo):

        page = Page.objects.get_by_name(name, False, True)
        if page.name in excluded_pages:
            # however these are not filtered before…
            return

        rev = page.revisions.all()[0]
        if page.trace > 1:
            # page is a subpage
            # create subdirectories
            for part in page.trace[:-1]:
                pth = path.join(rev.attachment and attachment_folder or
                                page_folder, *fix_path(part).split('/'))
                if not path.exists(pth):
                    os.mkdir(pth)

        if rev.attachment:
            # page is an attachment
            shutil.copyfile(rev.attachment.filename, path.join(pth,
                            path.split(rev.attachment.filename)[1]))
        else:
            # page is a normal text page
            f = file(fix_path(path.join(page_folder, '%s.xml' % page.name)), 'w+')
            content = rev.text.render(format='docbook')
            # perform some replacements to make links and images work
            content = INTERNAL_IMG_REGEX.sub(r'<imagedata fileref="./attachments'
                                             r'/\1', content)
            content = ABSOLUTE_LINK_REGEX.sub(handle_link, content)
            content = THUMBNAIL_REGEX.sub(handle_thumbnail, content)

            # TODO: Images inside links don't work

            f.write(tpl.render({
                'page': page,
                'content': content
            }).encode('utf-8'))
            f.close()
        processed.add(name)
        pb.update(percent)

    # write the final book file
    with open(fix_path(path.join(page_folder, '..', 'snapshot.xml')), 'w+') as fobj:
        tpl = jinja_env.get_template('snapshot/docbook_book.xml')
        content = tpl.render({'pages': processed, 'today': datetime.now()})
        fobj.write(content)


if __name__ == '__main__':
    create_snapshot('snapshot')
