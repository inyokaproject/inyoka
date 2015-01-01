#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    inyoka.scripts.jabber_bot
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2007-2015 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import print_function

import logging
import os
import sys

import zmq

from sleekxmpp import ClientXMPP


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
    """Starts the server."""

    debug = (len(sys.argv) == 2 and sys.argv[1] == '--debug')

    error = False
    required_keys = ('INYOKA_JABBER_ID', 'INYOKA_JABBER_PASSWORD', 'INYOKA_JABBER_BIND')
    for key in required_keys:
        if key not in os.environ:
            error = True
            sys.stderr.write('You need to set {key} in your environment!\n'.format(key=key))

    if error:
        return 1

    jid = os.environ['INYOKA_JABBER_ID']
    password = os.environ['INYOKA_JABBER_PASSWORD']
    bind = os.environ['INYOKA_JABBER_BIND']

    level = logging.INFO if not debug else logging.DEBUG
    logging.basicConfig(level=level,
                        format='%(levelname)-8s %(message)s')

    xmpp = JabberBot(jid, password, bind)
    xmpp.connect()
    xmpp.process(block=True)


if __name__ == '__main__':
    sys.exit(main())
