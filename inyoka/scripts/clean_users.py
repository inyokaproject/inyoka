#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    inyoka.scripts.clean_expired_users
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    A simple script that searches for non activated users whose
    activation key is expired and deletes them.

    :copyright: (c) 2007-2013 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import sys
from datetime import datetime, timedelta
import time
from django.conf import settings


def get_expired_users():
    from inyoka.portal.user import User
    current_datetime = datetime.fromtimestamp(time.time())
    delta_to_activate = timedelta(hours=settings.ACTIVATION_HOURS)

    for user in User.objects.filter(status=0):
        if (current_datetime - user.date_joined) > delta_to_activate:
            if not _user_has_content(user):
                yield user


def _precheck_user_on_forum(user):
    from inyoka.forum.models import Topic, Post
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


def get_inactive_users(excludes=None):
    from inyoka.portal.user import User
    current_datetime = datetime.fromtimestamp(time.time())
    delta = timedelta(days=settings.USER_INACTIVE_DAYS)

    excludes = set(u.id for u in excludes) if excludes else set()

    for user in User.objects.filter(status=1).exclude(id__in=excludes).all():
        if user.last_login and (current_datetime - user.last_login) < delta:
            continue

        if not user.last_login:
            # there are some users with no last login, set it to a proper value
            user.last_login = current_datetime
            user.save()
        if not _user_has_content(user):
            yield user


if __name__ == '__main__':
    users_to_delete = []
    expired = tuple(get_expired_users())
    inactive = tuple(get_inactive_users())
    print "expired users: %s" % len(expired)
    print "users counted as inactive: %s" % len(inactive)
    print "users deletable: %s" % (len(expired + inactive))
    if '--delete' in sys.argv:
        for user in set((expired + inactive)):
            try:
                user.delete()
            except Exception as exc:
                print "EXCEPTION RAISED ON USER %s" % user
                print exc
