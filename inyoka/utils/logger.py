# -*- coding: utf-8 -*-
"""
    inyoka.utils.logger
    ~~~~~~~~~~~~~~~~~~~

    This module provides a logger.

    :copyright: (c) 2007-2015 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import logging

from django.conf import settings

from celery.signals import task_failure

logger = logging.getLogger(settings.INYOKA_LOGGER_NAME)

try:
    from raven.contrib.django.handlers import SentryHandler
except ImportError:
    SentryHandler = None

if not settings.DEBUG and SentryHandler is not None:
    logging_handler = SentryHandler()
    logging_handler.setLevel(logging.WARNING)
else:
    tmpl = '[%(asctime)s] %(levelname)s:%(name)s: %(message)s'
    logging_handler = logging.StreamHandler()
    logging_handler.setFormatter(logging.Formatter(tmpl))
    logging_handler.setLevel(logging.DEBUG)
logger.addHandler(logging_handler)


sentry_logger = logging.getLogger('sentry.errors')
sentry_logger.addHandler(logging.StreamHandler())


def process_failure_signal(sender, task_id, exception, args, kwargs, traceback,
                           einfo, signal=None):
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

task_failure.connect(process_failure_signal)
