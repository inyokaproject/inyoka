# -*- coding: utf-8 -*-
"""
    tests.apps.privmsg.test_notifications
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test privmsg notification.

    :copyright: (c) 2011-2016 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from mock import patch

from django.utils.translation import ugettext as _

from inyoka.utils.test import TestCase
from inyoka.portal.user import User
from inyoka.privmsg.notifications import send_privmsg_notification


class TestNotifications(TestCase):
    """
    Unit Test for sending notifications about new private messages.
    """

    @patch('inyoka.privmsg.notifications.queue_notifications.delay')
    def test_send_privmsg_notification(self, mock_delay):
        recipient = User(id=1, username='recipient')
        author = User(id=2, username='author')
        subject = 'subject'
        url = 'http://testhost/'
        template_data = {
            'author': author,
            'subject': subject,
            'url': url,
        }

        send_privmsg_notification(recipient, author, subject, url)

        mock_delay.assert_called_once_with(
            request_user_id=recipient.id,
            template='new_privmsg',
            subject=_(u'New private message from {author}: {subject}').format(**template_data),
            args=template_data,
        )
