# -*- coding: utf-8 -*-
"""
    inyoka.utils.logger
    ~~~~~~~~~~~~~~~~~~~

    This module provides a logger.

    :copyright: (c) 2007-2012 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import logging
from django.conf import settings
from celery.signals import task_failure
from raven.contrib.django import DjangoClient


class InyokaClient(DjangoClient):
    """Sentry client for Inyoka."""
    def get_user_info(self, request):
        if request.user.is_authenticated:
            user_info = {
                'is_authenticated': True,
                'id': request.user.pk,
                'username': request.user.username,
                'email': request.user.email,
            }
        else:
            user_info = {
                'is_authenticated': False,
            }
        return user_info


logger = logging.getLogger(settings.INYOKA_LOGGER_NAME)


if not settings.DEBUG:
    from raven.contrib.django.handlers import SentryHandler
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

# Advanced Celery Logging

def process_failure_signal(sender, task_id, exception, args, kwargs, traceback,
                           einfo, signal=None):
    exc_info = (type(exception), exception, traceback)
    logger.error('Celery job exception: %s (%s)' % (exception.__class__.__name__, exception),
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
