#-*- coding: utf-8 -*-
from datetime import datetime, timedelta
from celery.task import periodic_task
from celery.task.schedules import crontab
from inyoka.portal.models import SessionInfo
from inyoka.utils.sessions import SESSION_DELTA


@periodic_task(run_every=crontab(minute='*/5'))
def clean_sessions():
    last_change = (datetime.utcnow() - timedelta(seconds=SESSION_DELTA))
    SessionInfo.objects.filter(last_change__lt=last_change).delete()
