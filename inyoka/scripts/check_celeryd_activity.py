#-*- coding: utf-8 -*-
import sys
from datetime import datetime
from celery.app import current_app
from djcelery.models import PeriodicTask


def check_activity():
    task = PeriodicTask.objects.get(name='inyoka.tasks.activity_monitor')
    due, delta = task.schedule.is_due(task.last_run_at)
    seconds = (task.schedule.nowfun() - task.last_run_at).seconds
    interval = current_app().conf['CELERYBEAT_MAX_LOOP_INTERVAL']
    if seconds <= interval:
        return 0
    elif seconds > interval and seconds <= interval * 2:
        return 1
    else:
        return 2


if __name__ == '__main__':
    sys.exit(check_activity())
