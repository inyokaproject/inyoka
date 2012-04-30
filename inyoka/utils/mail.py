# -*- coding: utf-8 -*-
"""
    inyoka.utils.mail
    ~~~~~~~~~~~~~~~~~

    This module provides various e-mail related functionality.

    :copyright: (c) 2007-2012 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import re
from subprocess import Popen, PIPE
from django.conf import settings
from django.core.mail import send_mail as django_send_mail
from django.core.mail.backends.base import BaseEmailBackend


_mail_re = re.compile(r'''(?xi)
    (?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+
        (?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|
        "(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|
          \\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@
''')


def send_mail(subject, message, sender, to):
    assert len(to) == 1

    # Do not attempt to send to invalid email addresses
    # (may occur for disabled users)
    if to[0].endswith('.invalid') or not '@' in to[0]:
        return

    if settings.DEBUG_NOTIFICATIONS:
        print "Subject: %s\nMessage:%s\n\nSender: %s\nTo: %s" % (
              subject, message, sender, to)
    else:
        django_send_mail(subject, message, sender, to,
                         fail_silently=not settings.DEBUG)


def may_be_valid_mail(email):
    """
    Check if the mail may be valid.  This does not check the hostname part
    of the email, for that you still have to test with `may_accept_mails`.
    """
    return _mail_re.match(email) is not None


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
            proc = Popen(['/usr/sbin/sendmail', '-f', settings.INYOKA_SYSTEM_USER_EMAIL, '-t'], stdin=PIPE)
            proc.stdin.write(email_message.message().as_string())
            proc.stdin.flush()
            proc.stdin.close()
            # replace with os.wait() in a outer level to not wait to much?!
            proc.wait()
        except:
            if not self.fail_silently:
                raise
            return False
        return True
