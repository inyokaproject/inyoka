# -*- coding: utf-8 -*-
"""
    inyoka.utils.flashing
    ~~~~~~~~~~~~~~~~~~~~~

    Implements a simple system to flash messages.

    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.utils.local import current_request


def flash(message, success=None, classifier=None, session=None):
    """
    Flash a message (can contain XHTML).  If ``success`` is True, the flashbar
    will be green, if it's False, it will be red and if it's undefined it will
    be yellow.  If a classifier is given it can be used to unflash all
    messages with that classifier using the `unflash` method.
    """
    if session is None:
        session = getattr(current_request, 'session', None)
        if session is None:
            return False
    if not 'flmsg' in session:
        session['flmsg'] = [
            (message, success, classifier)
        ]
    else:
        session['flmsg'].append(
            (message, success, classifier)
        )
        session.modified = True
    return True


def unflash(classifier):
    """Unflash all messages with a given classifier"""
    session = getattr(current_request, 'session', None)
    if session is None:
        return
    session['flmsg'] = [item for item in session.get(
                                   'flmsg', ())
                                   if item[2] != classifier]
    if not session['flmsg']:
        del session['flmsg']


def clear():
    """Clear the whole flash buffer."""
    session = getattr(current_request, 'session', None)
    if session is not None:
        session.pop('flmsg', None)


def get_flashed_messages():
    """Get all flashed messages for this user."""
    request = current_request._get_current_object()
    flash_buffer = getattr(request, 'flash_message_buffer', None)
    if flash_buffer is not None:
        return flash_buffer
    session = getattr(request, 'session', None)
    if session is None:
        return []
    flash_buffer = [FlashMessage(x[0], x[1]) for x in
                    session.get('flmsg', ())]
    session.pop('flmsg', None)
    request.flash_message_buffer = flash_buffer
    return flash_buffer


def has_flashed_messages():
    """True if the request has flashed messages."""
    session = getattr(current_request, 'session', None)
    return bool(session and session.get('flmsg'))


class FlashMessage(object):
    __slots__ = ('text', 'success')

    def __init__(self, text, success=None):
        self.text = text
        self.success = success

    def __repr__(self):
        return '<%s(%s:%s)>' % (
            self.__class__.__name__,
            self.text,
            self.success
        )
