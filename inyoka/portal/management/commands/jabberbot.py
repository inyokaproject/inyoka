"""
    inyoka.portal.jabberbot
    ~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2007-2023 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import ssl
import sys
import zmq
import certifi
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from slixmpp import ClientXMPP

from inyoka.utils.logger import logger


class JabberBot(ClientXMPP):

    def __init__(self, jid, password, bind):
        ClientXMPP.__init__(self, jid, password)
        self.add_event_handler('session_start', self.handle_session_start)
        self.add_event_handler('disconnected', self.handle_disconnected)
        self.register_plugin('xep_0030')  # Service Discovery
        self.register_plugin('xep_0199')  # XMPP Ping
        self.zmq = zmq.Context()
        self.zeromq_bind = bind
        self.ssl_version = ssl.PROTOCOL_TLSv1_2
        self.ca_certs = certifi.where()

        logger.debug('Starting ZeroMQ Connection')
        self.zmq_socket = self.zmq.socket(zmq.REP)
        self.zmq_socket.setsockopt(zmq.LINGER, 0)
        logger.debug('Connecting to ZeroMQ Socket')
        self.zmq_socket.bind(self.zeromq_bind)

    def handle_session_start(self, event):
        self.send_presence()

        self.schedule("handle_mq", 5, self.handle_mq, repeat=True)

    def handle_mq(self):
        successful = False
        try:
            message = self.zmq_socket.recv_json()
            self.send_message(mto=message['jid'], mtype='chat',
                              mbody=message['body'])
            successful = True
        except zmq.ZMQError as exc:
            if not exc.errno == zmq.ETERM:
                raise
            return
        finally:
            try:
                self.zmq_socket.send_json({'successfull': successful})
            except zmq.ZMQError as exc:
                if not exc.errno == zmq.ETERM:
                    raise
                return

    def handle_disconnected(self, data):
        logger.info('DISCONNECTED :: %s' % data)
        self.zmq.term()
        # reset the context, since the bot automatically reconnects!
        self.zmq = zmq.Context()


class Command(BaseCommand):
    """
    Custom Management Command for our Jabber Bot Service. Requires no arguments and logs
    everything with django logging.
    """
    help = 'Jabberbot Service'

    def handle(self, *args, **kwargs):
        if args:
            raise CommandError("Command doesn't accept any arguments")

        if not (settings.JABBER_ID and settings.JABBER_PASSWORD and settings.JABBER_BIND):
            logger.warning('Jabberbot Configuration missing or incomplete.')
            raise SystemExit(1)
        xmpp = JabberBot(settings.JABBER_ID, settings.JABBER_PASSWORD, settings.JABBER_BIND)
        xmpp.connect()
        xmpp.process()
