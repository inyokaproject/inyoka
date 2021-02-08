# -*- coding: utf-8 -*-
"""
    inyoka.utils.logger
    ~~~~~~~~~~~~~~~~~~~

    This module provides a logger.

    :copyright: (c) 2007-2021 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import logging

from celery.signals import task_failure

logger = logging.getLogger('inyoka')


@task_failure.connect
def process_failure_signal(sender, task_id, exception, traceback, einfo, *args, **kwargs):
    exc_info = (type(exception), exception, traceback)
    descr = (exception.__class__.__name__, exception)
    logger.error('Celery job exception: %s (%s)' % descr,
        exc_info=exc_info,
        extra={
            'data': {
                'task_id': task_id,
                'sender': sender,
                'args': args,
                'kwargs': kwargs,
            }
        }
    )
