# -*- coding: utf-8 -*-
"""
    inyoka.utils.mail
    ~~~~~~~~~~~~~~~~~

    This module provides various e-mail related functionality.

    :copyright: (c) 2007-2023 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.conf import settings
from django.core.mail import send_mail as django_send_mail

from inyoka.utils.logger import logger


def send_mail(subject, message, sender, to):
    assert len(to) == 1

    # Do not attempt to send to invalid email addresses
    # (may occur for disabled users)
    if to[0].endswith('.invalid') or '@' not in to[0]:
        return

    logger.debug(
        "Subject: %s\nMessage:%s\n\nSender: %s\nTo: %s" %
                (subject, message, sender, to)
    )
    if not settings.DEBUG_NOTIFICATIONS:
        django_send_mail(subject, message, sender, to,
                         fail_silently=not settings.DEBUG)


def is_blocked_host(email_or_host):
    """
    This function checks the email or host against a blacklist of hosts that
    is configurable in the admin panel.
    """
    from inyoka.utils.storage import storage
    host = email_or_host.rsplit('@', 1)[-1]
    blocked_hosts = storage['blocked_hosts']
    return blocked_hosts and host in blocked_hosts.split()
