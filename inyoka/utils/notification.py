# -*- coding: utf-8 -*-
"""
    inyoka.utils.notification
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2007-2013 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings
from inyoka.utils.mail import send_mail
from inyoka.utils.jabber import send as send_jabber
from inyoka.utils.templating import render_template
from inyoka.portal.models import Subscription


def send_notification(user, template_name=None, subject=None, args=None):
    """
    Send a message to the user using the person's favorite method(s) specified
    in the user control panel.

    The message will be loaded from the file ``<template_name>.txt`` or
    ``<template_name>.jabber.txt`` respectively. Besides the template data
    provided via ``args`` the following data will be propagated to the template
    rendering process:

    ``domain``
        Resolves to the :data:`BASE_DOMAIN_NAME` as defined in the settings.

    ``username``
        Resolves to the username of the receiver.

    :param User user: An instance of a :class:`~inyoka.portal.user.User` model
        specifying the receiver of the notification.
    :param str template_name: The name of the mail/jabber template to use (w/o
        the file extension)
    :param str subject: The subject used in mails
    :param dict args: The data that is used during message template rendering
    """
    assert subject is not None
    args = args or {}

    if user.is_deleted:
        return

    methods = user.settings.get('notify', ['mail'])

    args.update({
        'domain': settings.BASE_DOMAIN_NAME,
        'username': user.username,
    })

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

    from django.db.models import Q

    if not include_notified:
        if isinstance(filter, Q):
            filter = filter & Q(notified=False)
        else:
            filter.update({'notified': False})

    if exclude_current_user:
        if not exclude:
            exclude = {'user__id': request_user_id}
        else:
            if 'user__id' in exclude:
                ids = [exclude.pop('user__id'), request_user_id] + exclude.pop('user__in', [])
                exclude.update({'user__in': ids})
            else:
                exclude.update({'user__id': request_user_id})

    if isinstance(filter, Q):
        subscriptions = Subscription.objects.filter(filter)
    else:
        subscriptions = Subscription.objects.filter(**filter)

    if exclude is not None:
        subscriptions = subscriptions.exclude(**exclude)

    notified_users = set()

    notified = set()
    for subscription in subscriptions.all():
        if subscription.user in notified_users:
            # Prevent duplicate notification for same event,
            # but update all subscriptions
            notified.add(subscription.id)
            continue
        notified_users.add(subscription.user)
        if callable(args):
            args = args(subscription)
        notify_about_subscription(subscription, template, subject, args)
        notified.add(subscription.id)

    if not include_notified:
        Subscription.objects.filter(id__in=notified).update(notified=True)

    if 'user__in' in exclude:
        notified_users.update(set(exclude['user__in']))

    if callback is not None:
        subtask(callback).delay(notified_users)

    return notified_users
