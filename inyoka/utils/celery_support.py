# -*- coding: utf-8 -*-
"""
    inyoka.utils.celery_support
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Module to add some workarounds for bugs regarding pickle and
    it's usage in serialization in django-kombu.

    :copyright: (c) 2007-2012 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import base64
from Queue import Empty
from djkombu.transport import Channel as KChannel, \
    DatabaseTransport as KDatabaseTransport
from djkombu.models import Queue
from django.utils import simplejson as json


class Channel(KChannel):
    """A new implementation that serializes a payload to proper base64.

    This fixes some unicode/utf8 encoding errors if we have some
    broken pickle data.
    """

    def _put(self, queue, message, **kwargs):
        message['body'] = base64.b64encode(message['body'])
        Queue.objects.publish(queue, json.dumps(message))

    def _get(self, queue):
        self.refresh_connection()
        message = Queue.objects.fetch(queue)
        if message:
            message = json.loads(message)
            message['body'] = base64.b64decode(message['body'])
            return message
        raise Empty()


class DatabaseTransport(KDatabaseTransport):
    Channel = Channel
