# -*- coding: utf-8 -*-
"""
    inyoka.forum.notifications
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Utilities for forum notifications.

    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from celery.task import task
from inyoka.utils import ctype
from inyoka.utils.notification import queue_notifications


def send_newtopic_notifications(user, post, topic, forum):
    from inyoka.portal.models import User
    # NOTE: we always notify about new topics, even if the forum was
    # not visited, because unlike the posts you won't see
    # other new topics

    data={'author_unsubscribe': post.author.get_absolute_url('unsubscribe'),
          'author_username': post.author.username,
          'forum_id': forum.id,
          'forum_name': forum.name,
          'forum_unsubscribe': forum.get_absolute_url('unsubscribe'),
          'post_url': post.get_absolute_url(),
          'topic_title': topic.title,
          'topic_version': topic.get_ubuntu_version(),
          'topic_version_number': topic.get_ubuntu_version().number}

    queue_notifications.delay(user.id, 'user_new_topic',
        u'Neues Thema vom Benutzer %s' % data.get('author_username'),
        data,
        include_notified=True,
        filter={'content_type': ctype(User), 'object_id': user.id},
        callback=notify_forum_subscriptions.subtask(args=(user.id, data)))


@task
def notify_forum_subscriptions(notified_users, request_user_id, data):
    from inyoka.forum.models import Forum

    # Inform users who subscribed to the forum
    queue_notifications.delay(request_user_id, 'new_topic',
        u'Neues Thema im Forum %s: „%s”' % (data.get('forum_name'), data.get('topic_title')),
        data,
        include_notified=True,
        filter={'content_type': ctype(Forum), 'object_id': data.get('forum_id')},
        callback=notify_ubuntu_version_subscriptions.subtask(args=(request_user_id, data)),
        exclude={'user__in': notified_users})


@task
def notify_ubuntu_version_subscriptions(notified_users, request_user_id, data):
    if data.get('topic_version') is not None:
        queue_notifications.delay(request_user_id, 'new_topic_ubuntu_version',
            u'Neues Thema mit der Version %s: „%s”' % (data.get('topic_version'), data.get('topic_title')),
            data,
            include_notified=True,
            filter={'ubuntu_version': data.get('topic_version_number')},
            exclude={'user__in': notified_users})


def send_edit_notifications(user, post, topic, forum):
    from inyoka.forum.models import Topic

    data={'author_unsubscribe': post.author.get_absolute_url('unsubscribe'),
          'author_username': post.author.username,
          'forum_name': forum.name,
          'post_url': post.get_absolute_url(),
          'topic_id': topic.id,
          'topic_title': topic.title,
          'topic_unsubscribe': topic.get_absolute_url('unsubscribe')}

    # notify about new answer in topic for topic-subscriptions
    queue_notifications.delay(user.id, 'new_post',
        u'Neue Antwort im Thema „%s”' % data.get('topic_title'),
        data,
        filter={'content_type': ctype(Topic), 'object_id': data.get('topic_id')},
        callback=notify_member_subscriptions.subtask(args=(user.id, data)))


@task
def notify_member_subscriptions(notified_users, request_user_id, data):
    from inyoka.portal.models import User
    # notify about new answer in topic for member-subscriptions
    queue_notifications.delay(request_user_id, 'user_new_post',
        u'Neue Antwort vom Benutzer „%s”' % data.get('author_username'),
        data, include_notified=True,
        filter={'content_type': ctype(User), 'object_id': request_user_id},
        exclude={'user__in': notified_users})


def send_discussion_notification(user, page):
    from inyoka.wiki.models import Page
    data={'creator': user.username,
          'page_id': page.id,
          'page_title': page.title,
          'page_unsubscribe': page.get_absolute_url('unsubscribe'),
          'topic_unsubscribe': page.topic.get_absolute_url('subscribe'),
          'topic_url': page.topic.get_absolute_url()}

    # also notify if the user has not yet visited the page,
    # since otherwise he would never know about the topic
    queue_notifications.delay(user.id, 'new_page_discussion',
        u'Neue Diskussion für die Seite „%s” wurde eröffnet' % data.get('page_title'),
        data,
        filter={'content_type': ctype(Page), 'object_id': data.get('page_id')})


def send_deletion_notification(user, topic, reason):
    from inyoka.forum.models import Topic
    data={'mod': user.username,
          'reason': reason,
          'topic_id': topic.id,
          'topic_title': topic.title}

    queue_notifications.delay(user.id, 'topic_deleted',
        u'Das Thema „%s” wurde gelöscht' % data.get('topic_title'),
        data,
        filter={'content_type': ctype(Topic), 'object_id': data.get('topic_id')})
