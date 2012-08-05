#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    inyoka.scripts.jabber_bot
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2007-2012 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import argparse
import sys
import logging

import zmq

from sleekxmpp import ClientXMPP


class JabberBot(ClientXMPP):

    def __init__(self, jid, password, bind):
        ClientXMPP.__init__(self, jid, password)
        self.add_event_handler('session_start', self.handle_session_start,
                               threaded=True)
        self.add_event_handler('disconnected', self.handle_disconnected)
        self.register_plugin('xep_0030') # Service Discovery
        self.register_plugin('xep_0199') # XMPP Ping
        self.zmq = zmq.Context()
        self.zeromq_bind = bind

    def handle_session_start(self, event):
        self.send_presence()

        logging.debug('Starting ZeroMQ Connection')
        socket = self.zmq.socket(zmq.REP)
        socket.setsockopt(zmq.LINGER, 0)
        logging.debug('Connecting to ZeroMQ Socket')
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
        logging.info('DISCONNECTED :: %s' % data)
        self.zmq.term()
        # reset the context, since the bot automatically reconnects!
        self.zmq = zmq.Context()


def main():
    """Parse arguments and start the server."""
    parser = argparse.ArgumentParser(description='Jabberbot')
    parser.add_argument('--jid', metavar='jid', type=unicode,
                        help='Jabber ID for the Bot',
                        required=True)
    parser.add_argument('--password', metavar='password', type=unicode,
                        help='Password for the JID',
                        required=True)
    parser.add_argument('--bind', metavar='bind', type=unicode,
                        help='Bind for the ZeroMQ endoint',
                        default='tcp://0.0.0.0:6203')
    parser.add_argument('--debug', action='store_true',
                        help='Activate debug mode')
    args = parser.parse_args()

    level = logging.INFO if not args.debug else logging.DEBUG
    logging.basicConfig(level=level,
                        format='%(levelname)-8s %(message)s')

    xmpp = JabberBot(args.jid, args.password, args.bind)
    xmpp.connect()
    xmpp.process(block=True)


if __name__ == '__main__':
    sys.exit(main())
