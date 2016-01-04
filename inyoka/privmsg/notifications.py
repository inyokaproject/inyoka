# -*- coding: utf-8 -*-
"""
    inyoka.privmsg.notifications
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Utilities for privmsg notifications.

    :copyright: (c) 2007-2016 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.utils.translation import ugettext as _

from inyoka.utils.notification import queue_notifications


def send_privmsg_notification(recipient, author, subject, url):
    data = {'author': author,
            'subject': subject,
            'url': url}

    queue_notifications.delay(
        recipient.id,
        'new_privmsg',
        _(u'New private message from {author}: {subject}').format(
            author=author,
            subject=subject),
        data
    )
