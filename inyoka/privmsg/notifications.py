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
    """Send notification about new private messages to the recipient."""
    template_data = {
        'author': author,
        'subject': subject,
        'url': url,
    }

    queue_notifications.delay(
        request_user_id=recipient.id,
        template='new_privmsg',
        subject=_(u'New private message from {author}: {subject}').format(**template_data),
        args=template_data,
    )
