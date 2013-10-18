# -*- coding: utf-8 -*-
"""
    inyoka.forum.notifications
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Utilities for forum notifications.

    :copyright: (c) 2007-2013 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from django.conf import settings
from django.utils import translation
from django.utils.translation import ugettext as _

from celery.task import task
from inyoka.utils import ctype
from inyoka.utils.notification import queue_notifications, send_notification
from inyoka.utils.urls import href


def send_newtopic_notifications(user, post, topic, forum):
    from inyoka.portal.models import User
    # NOTE: we always notify about new topics, even if the forum was
    # not visited, because unlike the posts you won't see
    # other new topics

    version_number = topic.get_ubuntu_version()

    data = {'author_unsubscribe': post.author.get_absolute_url('unsubscribe'),
          'author_username': post.author.username,
          'forum_id': forum.id,
          'forum_name': forum.name,
          'forum_unsubscribe': forum.get_absolute_url('unsubscribe'),
          'link_user_settings': href('portal', 'usercp', 'settings'),
          'post_url': post.get_absolute_url(),
          'topic_title': topic.title,
          'topic_version': topic.get_ubuntu_version(),
          'topic_version_number': version_number.number if version_number else None}

    queue_notifications.delay(user.id, 'user_new_topic',
        _(u'%(username)s has created a new topic') % {
            'username': data.get('author_username')},
        data,
        include_notified=True,
        filter={'content_type': ctype(User), 'object_id': user.id},
        callback=notify_forum_subscriptions.subtask(args=(user.id, data)))


@task(ignore_result=True)
def notify_forum_subscriptions(notified_users, request_user_id, data):
    from inyoka.forum.models import Forum
    prev_language = translation.get_language()
    translation.activate(settings.LANGUAGE_CODE)
    try:
        # Inform users who subscribed to the forum
        queue_notifications.delay(request_user_id, 'new_topic',
            _(u'New topic in forum “%(forum)s”: “%(topic)s”') % {
                    'forum': data.get('forum_name'),
                    'topic': data.get('topic_title')},
            data,
            include_notified=True,
            filter={'content_type': ctype(Forum),
                      'object_id': data.get('forum_id')},
            callback=notify_ubuntu_version_subscriptions.subtask(
                args=(request_user_id, data)),
            exclude = {'user__in': notified_users})
    finally:
        translation.activate(prev_language)


@task(ignore_result=True)
def notify_ubuntu_version_subscriptions(notified_users, request_user_id, data):
    prev_language = translation.get_language()
    translation.activate(settings.LANGUAGE_CODE)
    try:
        if data.get('topic_version') is not None:
            queue_notifications.delay(request_user_id, 'new_topic_ubuntu_version',
                _(u'New topic with version %(version)s: “%(topic)s”') % {
                    'version': data.get('topic_version'),
                    'topic': data.get('topic_title')},
                data,
                include_notified=True,
                filter={'ubuntu_version': data.get('topic_version_number')},
                exclude={'user__in': notified_users})
    finally:
        translation.activate(prev_language)


def send_edit_notifications(user, post, topic, forum):
    from inyoka.forum.models import Topic

    data = {'author_unsubscribe': post.author.get_absolute_url('unsubscribe'),
          'author_username': post.author.username,
          'forum_name': forum.name,
          'post_url': post.get_absolute_url(),
          'topic_id': topic.id,
          'topic_title': topic.title,
          'topic_unsubscribe': topic.get_absolute_url('unsubscribe')}

    # notify about new answer in topic for topic-subscriptions
    queue_notifications.delay(user.id, 'new_post',
        _(u'New reply in topic “%(topic)s”') % {
            'topic': data.get('topic_title')},
        data,
        filter={'content_type': ctype(Topic), 'object_id': data.get('topic_id')},
        callback=notify_member_subscriptions.subtask(args=(user.id, data)))


@task(ignore_result=True)
def notify_member_subscriptions(notified_users, request_user_id, data):
    from inyoka.portal.models import User
    # notify about new answer in topic for member-subscriptions
    #: TODO fix translation
    queue_notifications.delay(request_user_id, 'user_new_post',
        u'Neue Antwort vom Benutzer „%s”' % data.get('author_username'),
        data, include_notified=True,
        filter={'content_type': ctype(User), 'object_id': request_user_id},
        exclude={'user__in': notified_users})


def send_discussion_notification(user, page):
    from inyoka.wiki.models import Page
    data = {'creator': user.username,
          'page_id': page.id,
          'page_title': page.title,
          'page_unsubscribe': page.get_absolute_url('unsubscribe'),
          'topic_unsubscribe': page.topic.get_absolute_url('subscribe'),
          'topic_url': page.topic.get_absolute_url()}

    # also notify if the user has not yet visited the page,
    # since otherwise he would never know about the topic
    queue_notifications.delay(user.id, 'new_page_discussion',
        _(u'New discussion regarding the page “%(page)s” created') % {
            'page': data.get('page_title')},
        data,
        filter={'content_type': ctype(Page), 'object_id': data.get('page_id')})


def send_deletion_notification(user, topic, reason):
    from inyoka.forum.models import Topic
    data = {'mod': user.username,
          'reason': reason,
          'topic_id': topic.id,
          'topic_title': topic.title}

    queue_notifications.delay(user.id, 'topic_deleted',
        _(u'The topic “%(topic)s” has been deleted') % {
            'topic': data.get('topic_title')},
        data,
        filter={'content_type': ctype(Topic), 'object_id': data.get('topic_id')})


def send_reported_topics_notification(topic):
    data = {
        'reported_topics': href('forum', 'reported_topics'),
        'reporter': topic.reporter.username,
        'text': topic.reported,
        'topic_forum': topic.forum.name,
        'topic_link': topic.get_absolute_url(),
        'topic_title': topic.title,
    }
    notify_reported_topics.delay(data)


@task(ignore_result=True)
def notify_reported_topics(data):
    from inyoka.portal.models import User
    from inyoka.utils.storage import storage

    topic_title = data.get('topic_title')

    subscribers = storage['reported_topics_subscribers'] or u''
    uids = map(int, subscribers.split(','))
    for user in User.objects.filter(pk__in=uids).all():
        send_notification(user, 'new_reported_topic',
            _(u'Reported topic: “%(topic)s”') % {'topic': topic_title},
            data)


def send_move_notification(topic, old_forum, new_forum, request_user):
    from django.db.models import Q
    from inyoka.forum.models import Forum, Topic
    data = {
        'mod': request_user.username,
        'new_forum_name': new_forum.name,
        'old_forum_name': old_forum.name,
        'topic_link': topic.get_absolute_url(),
        'topic_title': topic.title,
    }

    # Send notification to topic author
    user_notifications = topic.author.settings.get('notifications', ('topic_move',))
    if 'topic_move' in user_notifications and topic.author != request_user:
        notify_move_author.delay(topic.author_id, data)

    # Send notifications to topic or forum subscribers
    queue_notifications.delay(
        request_user.pk,
        'topic_moved',
        _(u'The topic “%(topic)s” was moved') % {'topic': topic.title},
        data,
        filter=(Q(content_type=ctype(Topic)) & Q(object_id=topic.id)) |
               (Q(content_type=ctype(Forum)) & Q(object_id=topic.forum.id)),
        exclude={'user__id': topic.author_id})


@task(ignore_result=True)
def notify_move_author(author_id, data):
    from inyoka.portal.models import User
    try:
        author = User.objects.get(pk=author_id)
        topic_title = data.get('topic_title')
        send_notification(author, 'topic_moved',
            _(u'Your topic “%(topic)s” was moved') % {'topic': topic_title},
            data)
    except User.DoesNotExist:
        pass


def send_split_notification(old_topic, new_topic, is_new, request_user):
    from django.db.models import Q
    from inyoka.forum.models import Forum, Topic
    data = {
        'mod': request_user.username,
        'new_topic_title': new_topic.title,
        'new_topic_link': new_topic.get_absolute_url(),
        'old_topic_title': old_topic.title,
        'old_topic_link': old_topic.get_absolute_url(),
    }

    filter = Q(content_type=ctype(Topic)) & Q(object_id=old_topic.id)
    if is_new:
        filter |= (Q(content_type=ctype(Forum)) & Q(object_id=new_topic.forum.id))

    queue_notifications.delay(
        request_user.pk,
        'topic_splited',
        _(u'The topic “%(topic)s” was split') % {'topic': old_topic.title},
        data,
        filter=filter)
