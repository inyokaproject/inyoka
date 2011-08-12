#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Source line counter
    ~~~~~~~~~~~~~~~~~~~

    Count the lines of inyoka.

    :copyright: 2006-2007 by Armin Ronacher, 2008-2009 by Christopher Grebs.
    :license: GNU GPL, see LICENSE for more details.
"""
import os
from os import path


def main(root, search):
    LOC = 0

    root = path.abspath(root)
    offset = len(root) + 1

    print '+%s+' % ('=' * 78)
    print '| Lines of Code %s |' % (' ' * 62)
    print '+%s+' % ('=' * 78)

    for folder in search:
        off = 78/2 - len(folder)
        print '+%s  %s  %s+' % ('-' * off, folder, '-' * (off + 1))
        folder = path.join(root, folder)
        folder_locs = LOC
        for base, dirname, files in os.walk(folder):
            for fn in files:
                fn = path.join(base, fn)
                if (fn.endswith('.py') or fn.endswith('.js') or fn.endswith('.html')) and not 'migrations' in fn:
                    try:
                        fp = open(fn)
                        lines = sum(1 for l in fp.read().splitlines() if l.strip())
                    except:
                        print '%-70sskipped' % fn
                    else:
                        LOC += lines
                        print '| %-66s %7d   |' % (fn[offset:], lines)
                    fp.close()
        print '+-- %-56s Gesamt: %7d --+' % (' ' * off, LOC - folder_locs)

    print '+%s+' % ('-' * 78)
    print '| Total Lines of Code: %55d |' % LOC
    print '+%s+' % ('-' * 78)

if __name__ == '__main__':
    main('.', ['inyoka', 'extra', 'tests'])
