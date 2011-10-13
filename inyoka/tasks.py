#-*- coding: utf-8 -*-
"""
    inyoka.tasks
    ~~~~~~~~~~~~

    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from celery.task import periodic_task, task
from celery.task.schedules import crontab


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


@periodic_task(run_every=crontab(minute='*/1'))
def activity_monitor():
    """This task just does nothing but runs to get a simple monitoring"""
    return
