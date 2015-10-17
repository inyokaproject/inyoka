# -*- coding: utf-8 -*-
"""
    inyoka.portal.tasks
    ~~~~~~~~~~~~~~~~~~~~

    Celery Tasks for our Portal App.

    :copyright: (c) 2011-2015 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from time import time
from datetime import datetime, timedelta

from celery.task import periodic_task
from celery.task.schedules import crontab

from django.conf import settings

from inyoka.portal.models import SessionInfo
from inyoka.utils.sessions import SESSION_DELTA
from inyoka.utils.storage import storage
from inyoka.utils.logger import logger
from inyoka.portal.user import User
from inyoka.forum.models import Topic, Post


@periodic_task(run_every=crontab(minute='*/5'))
def clean_sessions():
    """Clean sessions older than SESSION_DELTA (300s)"""
    last_change = (datetime.utcnow() - timedelta(seconds=SESSION_DELTA))
    SessionInfo.objects.filter(last_change__lt=last_change).delete()


@periodic_task(run_every=crontab(minute='*/5'))
def check_for_user_record():
    """Checks whether the current session count is a new record."""
    delta = datetime.utcnow() - timedelta(seconds=SESSION_DELTA)
    record = int(storage.get('session_record', 0))
    session_count = SessionInfo.objects.filter(last_change__gt=delta).count()
    if session_count > record:
        storage['session_record'] = unicode(session_count)
        storage['session_record_time'] = int(time())


# FIXME: Should be run ever day.
@periodic_task(run_every=crontab(minute='*/5'))
def clean_expired_users():
    current_datetime = datetime.fromtimestamp(time())
    delta_to_activate = timedelta(hours=settings.ACTIVATION_HOURS)

    for user in User.objects.filter(status=0).exclude(username__in=set([settings.INYOKA_ANONYMOUS_USER, settings.INYOKA_SYSTEM_USER])).all():
        if (current_datetime - user.date_joined) > delta_to_activate:
            if not _user_has_content(user):
                logger.info('Deleting expiered User %s' % user.username)
                user.delete()


def _precheck_user_on_forum(user):
    topics = list(Topic.objects.filter(author=user).all())
    posts = list(Post.objects.filter(author=user).all())
    return topics or posts


def _user_has_content(user):
    counters = (
        # private messages
        user.privatemessageentry_set.count() > 0,
        # ikhaya articles
        user.article_set.count() > 0,
        # ikhaya article comments
        user.comment_set.count() > 0,
        # pastes
        user.entry_set.count() > 0,
        # created events
        user.event_set.count() > 0,
        # active suggestions to ikhaya articles
        user.suggestion_set.count() > 0,
        # user posts
        user.post_count > 0,
        # user wiki revisions
        user.wiki_revisions.count() > 0,
        # user subscriptions to threads/wikipages etc.
        user.subscription_set.count() > 0
    )

    if not any(counters):
        if not _precheck_user_on_forum(user):
            return False
    return True


# FIXME: Should be run ever week.
@periodic_task(run_every=crontab(minute='*/1'))
def clean_inactive_users():
    current_datetime = datetime.fromtimestamp(time())
    delta = timedelta(days=settings.USER_INACTIVE_DAYS)

    for user in User.objects.filter(status=1).exclude(username__in=set([settings.INYOKA_ANONYMOUS_USER, settings.INYOKA_SYSTEM_USER])).all():
        if user.last_login and (current_datetime - user.last_login) < delta:
            continue

        if not user.last_login:
            # there are some users with no last login, set it to a proper value
            user.last_login = current_datetime
            user.save()
        if not _user_has_content(user):
            logger.info('Deleting inactive User %s' % user.username)
            user.delete()
