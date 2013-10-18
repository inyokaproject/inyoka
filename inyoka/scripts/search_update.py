#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    inyoka.scripts.search_update
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This scripts updates the search index by (re)indexing the documents
    of `portal_searchqueue`.

    If the search index is not existent when starting this script, it
    automatically gets created; afterwards the index is completely generated
    for all documents of all components.

    :copyright: (c) 2007-2013 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from __future__ import division

import datetime
from operator import itemgetter

from django.conf import settings
from xapian import DatabaseOpeningError

from inyoka.portal.models import SearchQueue
from inyoka.utils import groupby
from inyoka.utils.search import search
from inyoka.utils.terminal import show


def update_index(component, docids):
    connection = search.get_connection(True)
    total = len(docids)
    print "Updating search index for %d documents on %s" % (
          total, datetime.datetime.utcnow())

    adapter = search.adapters[component]
    for start in range(0, total, settings.SEARCH_INDEX_BLOCKSIZE):
        end = min(start + settings.SEARCH_INDEX_BLOCKSIZE, total)
        show('  fetching...')
        objects = adapter.get_objects(docids[start:end])
        show('done - now indexing %s - %d of %d...' % (
             (start + 1, end, total)))
        search.index_objects(component, objects, connection)
        show('done\n')

        # finally a flush at the end of everything on a block basis
        connection.flush()

    # remove document ids from search queue once we got
    # them indexed.
    SearchQueue.objects.filter(doc_id__in=docids).delete()


def update():
    """
    Update the next items from the queue.  You should call this
    function regularly (e.g. as cron).
    """
    docs = groupby(SearchQueue.objects.values_list('doc_id', 'component'), itemgetter(1))
    for component, docids in docs.iteritems():
        update_index(component, docids)


def reindex(app=None):
    """Update the search index by reindexing all tuples from the database."""
    def index_comp(comp, adapter):
        print "\n\n"
        print "---------- indexing %s -----------------" % comp
        print "starting at %s" % datetime.datetime.now()
        print
        docids = list(adapter.get_doc_ids())
        update_index(comp, docids)

    if app:
        comp, adapter = app, search.adapters[app]
        index_comp(comp, adapter)
    else:
        for comp, adapter in search.adapters.iteritems():
            index_comp(comp, adapter)


if __name__ == '__main__':
    print "search update started"
    try:
        search.get_connection()
    except DatabaseOpeningError:
        print 'Search index does not exist, creating a new one'
        search.get_connection(True)
        print 'Starting to reindex everything'
        reindex()
    update()
    print "search updated finished at %s" % datetime.datetime.now()
