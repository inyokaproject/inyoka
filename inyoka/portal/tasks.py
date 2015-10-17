# -*- coding: utf-8 -*-
"""
    inyoka.portal.tasks
    ~~~~~~~~~~~~~~~~~~~~

    Celery Tasks for our Portal App.

    :copyright: (c) 2011-2015 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from time import time
from datetime import datetime, timedelta

from celery.task import periodic_task
from celery.task.schedules import crontab

from django.conf import settings

from inyoka.portal.models import SessionInfo
from inyoka.utils.sessions import SESSION_DELTA
from inyoka.utils.storage import storage
from inyoka.utils.logger import logger
from inyoka.portal.user import User


@periodic_task(run_every=crontab(minute='*/5'))
def clean_sessions():
    """Clean sessions older than SESSION_DELTA (300s)"""
    last_change = (datetime.utcnow() - timedelta(seconds=SESSION_DELTA))
    SessionInfo.objects.filter(last_change__lt=last_change).delete()


@periodic_task(run_every=crontab(minute='*/5'))
def check_for_user_record():
    """Checks whether the current session count is a new record."""
    delta = datetime.utcnow() - timedelta(seconds=SESSION_DELTA)
    record = int(storage.get('session_record', 0))
    session_count = SessionInfo.objects.filter(last_change__gt=delta).count()
    if session_count > record:
        storage['session_record'] = unicode(session_count)
        storage['session_record_time'] = int(time())


# FIXME: Should be run ever day.
@periodic_task(run_every=crontab(minute='*/5'))
def clean_expired_users():
    """
    Deletes all never activated Users, except system users. An user will be deleted
    after ACTIVATION_HOURS (default 48h).
    """
    current_datetime = datetime.fromtimestamp(time())
    delta_to_activate = timedelta(hours=settings.ACTIVATION_HOURS)

    for user in User.objects.filter(status=0).exclude(username__in=set([settings.INYOKA_ANONYMOUS_USER, settings.INYOKA_SYSTEM_USER])).all():
        if (current_datetime - user.date_joined) > delta_to_activate:
            if not user.has_content:
                logger.info('Deleting expiered User %s' % user.username)
                user.delete()


# FIXME: Should be run ever week.
@periodic_task(run_every=crontab(minute='*/1'))
def clean_inactive_users():
    """
    Deletes Users with no content and a last login more than USER_INACTIVE_DAYS (default one year)
    ago.
    """
    current_datetime = datetime.fromtimestamp(time())
    delta = timedelta(days=settings.USER_INACTIVE_DAYS)

    for user in User.objects.filter(status=1).exclude(username__in=set([settings.INYOKA_ANONYMOUS_USER, settings.INYOKA_SYSTEM_USER])).all():
        if user.last_login and (current_datetime - user.last_login) < delta:
            continue

        if not user.last_login:
            # there are some users with no last login, set it to a proper value
            user.last_login = current_datetime
            user.save()
        if not user.has_content:
            logger.info('Deleting inactive User %s' % user.username)
            user.delete()
