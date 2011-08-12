#-*- coding: utf-8 -*-
"""
    inyoka.tasks
    ~~~~~~~~~~~~

    Module that implements various `Celery <http://celeryproject.org>`_ backed
    tasks like email notifications.

    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
# register special logging
import inyoka.utils.logger

# register queue_notification task
import inyoka.utils.notification

# register forum notification tasks
import inyoka.forum.notifications

# register forum notification tasks
import inyoka.ikhaya.notifications

# register forum notification tasks
import inyoka.wiki.notifications
