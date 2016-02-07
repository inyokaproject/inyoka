# -*- coding: utf-8 -*-
"""
    inyoka.privmsg.tasks
    ~~~~~~~~~~~~~~~~~~~~

    Celery Tasks for our Portal App.

    :copyright: (c) 2011-2016 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from celery import shared_task
from inyoka.privmsg.models import Message, MessageData


@shared_task
def clean_abandoned_messages():
    """
    Delete abandoned messages of which no users have copies any more.
    """
    MessageData.objects.abandoned().all().delete()


@shared_task
def expunge_private_messages():
    """
    Delete old private messages from users trash folders.
    """
    Message.objects.to_expunge().all().delete()
