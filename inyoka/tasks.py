#-*- coding: utf-8 -*-
"""
    inyoka.tasks
    ~~~~~~~~~~~~

    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from celery.task import periodic_task
from celery.task.schedules import crontab


@periodic_task(run_every=crontab(minute='*/1'))
def activity_monitor():
    """This task just does nothing but runs to get a simple monitoring"""
    return
