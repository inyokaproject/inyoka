"""
    inyoka.portal.tasks
    ~~~~~~~~~~~~~~~~~~~~

    Celery Tasks for our Portal App.

    :copyright: (c) 2011-2025 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from datetime import timedelta
from time import time

from celery import shared_task
from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.utils import timezone as dj_timezone

from inyoka.portal.models import PrivateMessageEntry
from inyoka.portal.user import User
from inyoka.utils.logger import logger
from inyoka.utils.storage import storage


@shared_task
def check_for_user_record():
    """
    Checks whether the current session count is a new record.
    """
    record = int(storage.get('session_record', 0))
    session_count = len(cache.keys('sessioninfo:*'))
    if session_count > record:
        storage['session_record'] = str(session_count)
        storage['session_record_time'] = int(time())


@shared_task
def clean_expired_users():
    _clean_expired_users()

def _clean_expired_users():
    """
    Deletes all never activated Users, except system users. A user will be
    deleted after ACTIVATION_HOURS (default 48h).
    """
    expired_datetime = dj_timezone.now() - timedelta(hours=settings.ACTIVATION_HOURS)
    user_query = (User.objects.filter(status=User.STATUS_INACTIVE).filter(date_joined__lte=expired_datetime)
                     .exclude(username__in={settings.ANONYMOUS_USER_NAME, settings.INYOKA_SYSTEM_USER}))

    for user in user_query:
        if not user.has_content():
            logger.info(f'Deleting expired User {user.username}')
            user.delete()


@shared_task
def clean_inactive_users():
    _clean_inactive_users()

def _clean_inactive_users():
    """
    Deletes Users with no content and a last login more than
    USER_INACTIVE_DAYS (default one year) ago.
    """
    inactive_datetime = dj_timezone.now() - timedelta(days=settings.USER_INACTIVE_DAYS)
    user_query = (User.objects.filter(last_login__lte=inactive_datetime)
                  .exclude(username__in={settings.ANONYMOUS_USER_NAME, settings.INYOKA_SYSTEM_USER}))

    for user in user_query:
        if not user.has_content():
            logger.info(f'Deleting inactive User {user.username}')
            user.delete()


@shared_task
def query_counter_task(cache_key, sql):
    """
    Runs sql and saves the result to a specific redis key.

    Used be inyoka.utils.cache import QueryCounter.
    """
    cursor = connection.cursor()
    cursor.execute(sql)
    cache.set(cache_key, cursor.fetchone()[0])


@shared_task
def clean_privmsg_folders():
    """Clean private message folders."""
    logger.info("Deleting private messages after end of cache duration")
    PrivateMessageEntry.clean_private_message_folders()
