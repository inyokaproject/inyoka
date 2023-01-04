# -*- coding: utf-8 -*-
"""
    inyoka.portal.tasks
    ~~~~~~~~~~~~~~~~~~~~

    Celery Tasks for our Portal App.

    :copyright: (c) 2011-2023 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime, timedelta
from time import time

from celery import shared_task
from django.conf import settings
from django.core.cache import cache
from django.db import connection

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
    """
    Deletes all never activated Users, except system users. An user will be
    deleted after ACTIVATION_HOURS (default 48h).
    """
    expired_datetime = datetime.fromtimestamp(time()) - timedelta(hours=settings.ACTIVATION_HOURS)

    for user in (User.objects.filter(status=0)
                     .filter(date_joined__lte=expired_datetime)
                     .exclude(username__in=set([
                         settings.ANONYMOUS_USER_NAME,
                         settings.INYOKA_SYSTEM_USER]))):
        if not user.has_content():
            logger.info('Deleting expiered User %s' % user.username)
            user.delete()


@shared_task
def clean_inactive_users():
    """
    Deletes Users with no content and a last login more than
    USER_INACTIVE_DAYS (default one year) ago.
    """
    inactive_datetime = datetime.fromtimestamp(time()) - timedelta(days=settings.USER_INACTIVE_DAYS)

    for user in (User.objects
                     .filter(last_login__lte=inactive_datetime)
                     .exclude(username__in=set([
                         settings.ANONYMOUS_USER_NAME,
                         settings.INYOKA_SYSTEM_USER]))):
        if not user.has_content():
            logger.info('Deleting inactive User %s' % user.username)
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
