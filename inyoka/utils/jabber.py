# -*- coding: utf-8 -*-
"""
    inyoka.utils.jabber
    ~~~~~~~~~~~~~~~~~~~

    Helper functions to communicate with the bot.  The communication uses
    basic XMLRPC.

    :copyright: (c) 2007-2021 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import re

import zmq
from django.conf import settings

# NOTE: according to rfc4622 a nodeid is optional. But we require one
#       'cause nobody should enter a service-jid in the jabber field.
#       That way we don't need to validate the domain and resid.
_jabber_re = re.compile(r'(?xi)(?:[a-z0-9!$\(\)*+,;=\[\\\]\^`{|}\-._~]+)@')


def may_be_valid_jabber(jabber):
    return _jabber_re.match(jabber) is not None


def send(jid, message):
    """Send a plain text message to a JID."""
    context = zmq.Context()
    sender = context.socket(zmq.REQ)
    sender.connect(settings.JABBER_BOT_SERVER)
    sender.send_json({'jid': jid, 'body': message})
    # 500 ms are long enough to try sending data.
    sender.close(50)
    context.term()
