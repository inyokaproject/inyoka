# -*- coding: utf-8 -*-
"""
    inyoka.portal.jabberbot
    ~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2007-2020 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import ssl
import sys
import zmq
import certifi
from django.conf import settings
from django.core.management.base import NoArgsCommand
from sleekxmpp import ClientXMPP

from inyoka.utils.logger import logger


class JabberBot(ClientXMPP):

    def __init__(self, jid, password, bind):
        ClientXMPP.__init__(self, jid, password)
        self.add_event_handler('session_start', self.handle_session_start,
                               threaded=True)
        self.add_event_handler('disconnected', self.handle_disconnected)
        self.register_plugin('xep_0030')  # Service Discovery
        self.register_plugin('xep_0199')  # XMPP Ping
        self.zmq = zmq.Context()
        self.zeromq_bind = bind
        if sys.version_info >= (2, 7, 13):
            self.ssl_version = ssl.PROTOCOL_TLS
        else:
            self.ssl_version = ssl.PROTOCOL_SSLv23
        self.ca_certs = certifi.where()

    def handle_session_start(self, event):
        self.send_presence()

        logger.debug('Starting ZeroMQ Connection')
        socket = self.zmq.socket(zmq.REP)
        socket.setsockopt(zmq.LINGER, 0)
        logger.debug('Connecting to ZeroMQ Socket')
        socket.bind(self.zeromq_bind)

        while True:
            successfull = False
            try:
                message = socket.recv_json()
                self.send_message(mto=message['jid'], mtype='chat',
                                  mbody=message['body'])
                successfull = True
            except zmq.ZMQError as exc:
                if not exc.errno == zmq.ETERM:
                    raise
                break
            finally:
                try:
                    socket.send_json({'successfull': successfull})
                except zmq.ZMQError as exc:
                    if not exc.errno == zmq.ETERM:
                        raise
                    break

    def handle_disconnected(self, data):
        logger.info('DISCONNECTED :: %s' % data)
        self.zmq.term()
        # reset the context, since the bot automatically reconnects!
        self.zmq = zmq.Context()


class Command(NoArgsCommand):
    """
    Custom Management Command for our Jabber Bot Service. Requires no arguments and logs
    everything with django logging.
    """
    help = 'Jabberbot Service'

    def handle_noargs(self, *args, **kwargs):
        if not (settings.JABBER_ID and settings.JABBER_PASSWORD and settings.JABBER_BIND):
            logger.warning('Jabberbot Configuration missing or incomplete.')
            raise SystemExit(1)
        xmpp = JabberBot(settings.JABBER_ID, settings.JABBER_PASSWORD, settings.JABBER_BIND)
        xmpp.connect()
        xmpp.process(block=True)
