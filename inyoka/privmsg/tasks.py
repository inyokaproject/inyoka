# -*- coding: utf-8 -*-
"""
    inyoka.privmsg.tasks
    ~~~~~~~~~~~~~~~~~~~~

    Celery Tasks for our Portal App.

    :copyright: (c) 2011-2016 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from celery import shared_task

from inyoka.privmsg.models import Message


@shared_task
def expunge_private_messages():
    """
    Delete old private messages from users trash folder.
    """
    Message.objects.to_expunge().delete()
