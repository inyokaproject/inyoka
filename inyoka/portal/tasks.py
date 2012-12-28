#-*- coding: utf-8 -*-
from time import time
from datetime import datetime, timedelta
from celery.task import periodic_task
from celery.task.schedules import crontab
from inyoka.portal.models import SessionInfo
from inyoka.utils.sessions import SESSION_DELTA
from inyoka.utils.storage import storage


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