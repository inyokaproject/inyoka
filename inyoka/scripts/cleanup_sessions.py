#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    inyoka.scripts.cleanup_sessions
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Clean up unused sessions and session infos.

    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from datetime import datetime, timedelta
from inyoka.portal.models import SessionInfo
from inyoka.utils.sessions import SESSION_DELTA


def main():
    last_change = (datetime.utcnow() - timedelta(seconds=SESSION_DELTA))
    SessionInfo.objects.filter(last_change__lt=last_change).delete()


if __name__ == '__main__':
    main()
