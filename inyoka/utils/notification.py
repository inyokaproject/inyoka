# -*- coding: utf-8 -*-
"""
    inyoka.utils.notification
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2007-2013 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from django.conf import settings

from celery.task import task
from celery.task.sets import subtask

from inyoka.portal.models import Subscription
from inyoka.utils.jabber import send as send_jabber
from inyoka.utils.mail import send_mail
from inyoka.utils.templating import render_template


def send_notification(user, template_name=None, subject=None, args=None):
    """
    Send a message to the user using the person's favourite method(s)
    he has specified in the user control panel.
    """
    assert subject is not None
    args = args or {}

    if user.is_deleted:
        return

    methods = user.settings.get('notify', ['mail'])

    if 'jabber' in methods and user.jabber:
        message = render_template('mails/%s.jabber.txt' % template_name, args)
        send_jabber(user.jabber, message)
    if 'mail' in methods:
        message = render_template('mails/%s.txt' % template_name, args)
        send_mail(settings.EMAIL_SUBJECT_PREFIX + subject, message,
                  settings.INYOKA_SYSTEM_USER_EMAIL, [user.email])


def notify_about_subscription(sub, template=None, subject=None, args=None):
    args = args or {}
    if not sub.can_read:
        # don't send subscriptions to user that don't have read
        # access to the resource
        return
    send_notification(sub.user, template, subject, args)


@task
def queue_notifications(request_user_id, template=None, subject=None, args=None,
                        include_notified=False, exclude_current_user=True,
                        filter=None, exclude=None, callback=None):
    assert filter is not None
    assert args is not None

    if not include_notified:
        filter.update({'notified': False})

    if exclude_current_user:
        if not exclude:
            exclude = {'user__id': request_user_id}
        else:
            exclude.update({'user__id': request_user_id})

    subscriptions = Subscription.objects.filter(**filter)
    if exclude is not None:
        subscriptions = subscriptions.exclude(**exclude)

    notified_users = set()

    notified = set()
    for subscription in subscriptions.all():
        notified_users.add(subscription.user)
        if callable(args):
            args = args(subscription)
        args.update({'username': subscription.user.username})
        notify_about_subscription(subscription, template, subject, args)
        notified.add(subscription.id)

    if not include_notified:
        Subscription.objects.filter(id__in=notified).update(notified=True)

    if 'user__in' in exclude:
        notified_users.update(set(exclude['user__in']))

    if callback is not None:
        subtask(callback).delay(notified_users)

    return notified_users
