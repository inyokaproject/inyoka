#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    inyoka.scripts.clean_thumbnail_cache
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This script removes unused thumbnails from the wiki thumbnail cache.

    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.wiki.utils import clean_thumbnail_cache as clean_wiki_cache


def main():
    print 'Cleaning wiki thumbnail cache...',
    print '%d files deleted' % len(clean_wiki_cache())


if __name__ == '__main__':
    main()
