#-*- coding: utf-8 -*-
"""
    inyoka.tasks
    ~~~~~~~~~~~~

    Module that implements various `Celery <http://celeryproject.org>`_ backed
    tasks like email notifications.

    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from celery.task import task

# register special logging
import inyoka.utils.logger

# register queue_notification task
import inyoka.utils.notification

# register forum notification tasks
import inyoka.forum.notifications

# register forum notification tasks
import inyoka.ikhaya.notifications

# register forum notification tasks
import inyoka.wiki.notifications


@task
def update_index(docids, doctype_name, index_name):
    from inyoka.utils.search import search, autodiscover
    from django.conf import settings
    autodiscover()
    block_size = settings.SEARCH_INDEX_BLOCKSIZE
    index = search.indices[index_name]
    connection = search.get_connection()
    total = len(docids)
    for start in range(0, total, block_size):
        end = min(start + block_size, total)
        objects = index.type_map[doctype_name].get_objects(docids[start:end])
        for obj in objects:
            search.store(index, doctype_name, obj, bulk=True)
    connection.force_bulk()
    connection.refresh(index_name)
