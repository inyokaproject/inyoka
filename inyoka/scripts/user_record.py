#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    inyoka.scripts.user_record
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    This file checks for a new user record.
    It should be executed periodically by a cron.
"""
from time import time
from datetime import datetime, timedelta
from inyoka.utils.sessions import SESSION_DELTA
from inyoka.utils.storage import storage
from inyoka.portal.models import SessionInfo


def check_for_user_record():
    """
    Checks whether the current session count is a new record.
    This function should be called periodically (by a cron).
    """
    delta = datetime.utcnow() - timedelta(seconds=SESSION_DELTA)
    record = int(storage.get('session_record', 0))
    session_count = SessionInfo.objects.filter(last_change__gt=delta).count()
    if session_count > record:
        storage['session_record'] = unicode(session_count)
        storage['session_record_time'] = int(time())


if __name__ == '__main__':
    check_for_user_record()
