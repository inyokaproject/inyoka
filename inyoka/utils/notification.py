"""
    inyoka.utils.notification
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2007-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from celery import shared_task
from celery.canvas import subtask
from django.conf import settings
from django.template.loader import render_to_string

from inyoka.portal.models import Subscription
from inyoka.utils.logger import logger
from inyoka.utils.mail import send_mail


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

    if 'mail' in methods:
        message = render_to_string(f'mails/{template_name}.txt', args)
        send_mail(settings.EMAIL_SUBJECT_PREFIX + subject, message,
                  settings.INYOKA_SYSTEM_USER_EMAIL, [user.email])


def notify_about_subscription(sub, template=None, subject=None, args=None):
    args = args or {}
    forum_id = args.get('forum_id')

    if not sub.can_read(forum_id):
        # don't send subscriptions to user that don't have read
        # access to the resource
        return
    if template == 'topic_split' and 'topic_split' not in sub.user.settings.get('notifications', ('topic_split',)):
        return

    send_notification(sub.user, template, subject, args)


@shared_task
def queue_notifications(request_user_id, template=None, subject=None, args=None,
                        include_notified=False, exclude_current_user=True,
                        filter=None, exclude=None, callback=None):
    assert filter is not None
    assert args is not None

    if not include_notified:
        filter.update({'notified': False})

    # Filter subscriptions
    # It is important to use two exludes,
    # as a singe exclude statement excludes only the subscriptions
    # which fulfill all criteria
    subscriptions = Subscription.objects.filter(**filter)
    if exclude is not None:
        subscriptions = subscriptions.exclude(**exclude)
    if exclude_current_user:
        subscriptions = subscriptions.exclude(user_id=request_user_id)

    notified_users = set()
    notified = set()

    for subscription in subscriptions.all():
        user = subscription.user
        if user.id in notified_users:
            continue

        notified_users.add(user.id)
        if callable(args):
            args = args(subscription)
        args.update({'username': user.username})
        notify_about_subscription(subscription, template, subject, args)
        notified.add(subscription.id)

    if not include_notified:
        Subscription.objects.filter(id__in=notified).update(notified=True)

    if exclude and 'user_id__in' in exclude:
        notified_users.update(set(exclude['user_id__in']))

    if callback is not None:
        subtask(callback).delay(list(notified_users))

    logger.debug(f'Notified for {template}: {notified_users}')

    return list(notified_users)
