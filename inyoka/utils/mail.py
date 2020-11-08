# -*- coding: utf-8 -*-
"""
    inyoka.utils.mail
    ~~~~~~~~~~~~~~~~~

    This module provides various e-mail related functionality.

    :copyright: (c) 2007-2020 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from subprocess import PIPE, Popen

from django.conf import settings
from django.core.mail import send_mail as django_send_mail
from django.core.mail.backends.base import BaseEmailBackend

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


class SendmailEmailBackend(BaseEmailBackend):
    def __init__(self, fail_silently=False, **kwargs):
        super(SendmailEmailBackend, self).__init__(fail_silently=fail_silently)

    def open(self):
        return True

    def close(self):
        pass

    def send_messages(self, email_messages):
        """
        Sends one or more EmailMessage objects and returns the number of email
        messages sent.
        """
        if not email_messages:
            return
        num_sent = 0
        for message in email_messages:
            sent = self._send(message)
            if sent:
                num_sent += 1
        return num_sent

    def _send(self, email_message):
        """A helper method that does the actual sending."""
        if not email_message.recipients():
            return False
        try:
            cmd = ['/usr/sbin/sendmail',
                   '-f',
                   settings.INYOKA_SYSTEM_USER_EMAIL,
                   '-t']
            proc = Popen(cmd, stdin=PIPE)
            proc.stdin.write(email_message.message().as_bytes())
            proc.stdin.flush()
            proc.stdin.close()
            # replace with os.wait() in a outer level to not wait to much?!
            proc.wait()
        except:
            if not self.fail_silently:
                raise
            return False
        return True
