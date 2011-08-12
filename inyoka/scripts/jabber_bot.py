#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    inyoka.scripts.jabber_bot
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    This script provides the jabber bot we use.


    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import sys
import xmpp
import socket
import getpass
from datetime import datetime
from getopt import getopt, GetoptError
from os.path import basename
from xml.parsers.expat import ExpatError
from collections import deque
from SimpleXMLRPCServer import SimpleXMLRPCServer
from xmlrpclib import Fault


def log(msg):
    print >> sys.stderr, '[%s] %s' % (datetime.utcnow(), msg)


class ApplicationStop(KeyboardInterrupt):
    pass


class Bot(object):
    """
    The jabber bot.
    """

    def __init__(self, jid, password, addr, debug=False, srv=True):
        if debug:
            log('Connecting...')
        self.debug = debug
        jid = xmpp.protocol.JID(jid)
        self.queue = deque()
        self.client = xmpp.Client(jid.getDomain(), debug=[])
        try:
            self.client.connect(use_srv=srv)
            self.client.auth(jid.getNode(), password, jid.resource)
            self.client.sendInitPresence(requestRoster=False)
        except Exception, exc:
            msg = 'Could not connect: %s' % exc
            if self.debug:
                print log(msg)
            else:
                print msg
            raise ApplicationStop()

        self.xmlrpc = SimpleXMLRPCServer(addr)
        register = self.xmlrpc.register_function
        register(self.send_message, 'jabber.sendMessage')
        register(self.send_raw_message, 'jabber.sendRawMessage')

        if debug:
            log('Bot running')

    def send_message(self, jid, message):
        """
        This method is exported from the XMLRPC interface and used to add
        messages to the queue.  XHTML Data is parsed and added to the queue.
        """
        if isinstance(jid, basestring):
            jid = [jid]
        for jid in jid:
            self.queue.append(self.from_xhtml(jid, message))
            if self.debug:
                log('Added message for %r to queue [format=xhtml]' % (jid,))
        return True

    def send_raw_message(self, jid, message):
        """Send a raw (non XHTML) message."""
        if isinstance(jid, basestring):
            jid = [jid]
        for jid in jid:
            self.queue.append(xmpp.protocol.Message(jid, message, typ='chat'))
            if self.debug:
                log('Added message for %r to queue [format=raw]' % (jid,))
        return True

    def from_xhtml(self, jid, xhtml):
        """ DONT USE! IT'S BROKEN """
        """
        Helper method that creates a message object for this jid and the XHTML
        data.  Returns `None` if it cannot parse the XHTML.
        """
        try:
            node = xmpp.simplexml.XML2Node(u'<body xmlns="%s">%s</body>' % (
                'http://www.w3.org/1999/xhtml',
                xhtml
            ))
        except ExpatError, exc:
            raise Fault(1, str(exc))

        buffer = []

        def walk(nodes):
            for node in nodes:
                walk(node.getChildren())
                if isinstance(node.data, basestring):
                    buffer.append(node.data)
        walk(node.getChildren())

        msg = xmpp.protocol.Message(jid, u''.join(buffer), typ='chat')
        msg.addChild('html', {}, [node], xmpp.NS_XHTML_IM)
        return msg

    def serve_forever(self):
        """
        Serve the bot.
        """
        try:
            while 1:
                self.xmlrpc.handle_request()
                while self.queue:
                    msg = self.queue.popleft()
                    self.client.send(msg)
                    # Read data from stream
                    data = self.client.Process()
                    if self.debug:
                        log('Sent message to \'%s\', recv data %r' % (msg.getTo(), data))
        finally:
            exc_info = sys.exc_info()
            if exc_info and self.debug:
                log('Exception occurred: %s' % exc_info[1])
            self.client.disconnect()


def help():
    """Displays the help screen"""
    cmd = basename(sys.argv[0])
    print 'usage: %s [-j <jid>] [-p <password>] [-d] <address>' % cmd
    print '       %s -h' % cmd
    print
    print 'Extra options:'
    print '     --debug         synonym for -d'
    print '     --jid           synonym for -j'
    print '     --password      synonym for -p'
    print '     --help          show this screen'
    print '     --auto-reload   automatically restart on server errors'
    print
    print 'Start a new jabber bot for the inyoka portal. If no jid is given '
    print 'the loginname and the current hostname is used. If no password '
    print 'is provided the bot will ask for that password. This use useful '
    print 'if you don\'t want to have the password appear in top.'
    print
    print 'The address must be in the form hostname:port. The hostname part '
    print 'defaults to "localhost" and is optional.'
    return 0


def error(msg):
    """Display an error message."""
    print >> sys.stderr, 'error: %s' % msg
    return 1


def usage(extra):
    """Print an error message and the help."""
    error(extra)
    help()
    return 1


def main():
    """Parse arguments and start the server."""
    try:
        opts, args = getopt(sys.argv[1:], 'j:p:dh', ['jid=', 'password=',
                                                     'debug', 'auto-reload',
                                                     'help', 'no-srv'])
    except GetoptError, exc:
        return usage(unicode(exc))
    hostname = args and args[0] or None
    jid = password = None
    debug = auto_reload = False
    srv = True

    for option, value in opts:
        if option in ('-j', '--jid'):
            jid = value
        elif option in ('-p', '--password'):
            password = value
        elif option in ('-d', '--debug'):
            debug = True
        elif option == '--auto-reload':
            auto_reload = True
        elif option == '--no-srv':
            srv = False
        elif option in ('-h', '--help'):
            return help()

    if not hostname:
        return usage('no hostname given')
    elif not ':' in hostname:
        return usage('invalid format for hostname: %r' % hostname)
    else:
        hostname, port = hostname.rsplit(':', 1)
        hostname = hostname or 'localhost'
        try:
            port = int(port)
        except ValueError:
            return usage('invalid format for port number')
        print hostname, port
    if not jid:
        jid = '%s@%s' % (getpass.getuser(), socket.gethostname())
    if password is None:
        password = getpass.getpass('Password for %s: ' % jid)

    make_bot = lambda: Bot(jid, password, (hostname, port), debug, srv)
    while 1:
        try:
            make_bot().serve_forever()
        except KeyboardInterrupt:
            if debug:
                log('Shutting down bot')
            return 0
        except:
            if not auto_reload:
                raise
            if debug:
                log('Restarting bot')


if __name__ == '__main__':
    sys.exit(main())
