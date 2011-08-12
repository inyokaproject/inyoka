# -*- coding: utf-8 -*-
"""
    inyoka.wiki.notifications
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Utilities for wiki notifications.

    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from celery.task import task
from inyoka.utils import ctype
from inyoka.utils.notification import queue_notifications


def send_new_suggestion_notifications(user, suggestion):
    from inyoka.ikhaya.models import Suggestion
    data={'suggestion_author': suggestion.author.username,
          'suggestion_title': suggestion.title,
          'suggestion_url': suggestion.get_absolute_url()}

    queue_notifications.delay(user.id, 'new_suggestion',
        u'Neuer Artikelvorschlag „%s” ' % data.get('suggestion_title'),
        data,
        filter={'content_type': ctype(Suggestion)})


def send_comment_notifications(user, comment, article):
    from inyoka.ikhaya.models import Article
    data={'article_id': article.id,
          'article_subject': article.subject,
          'article_unsubscribe': article.get_absolute_url('unsubscribe'),
          'comment_author': comment.author,
          'comment_url': comment.get_absolute_url()}

    queue_notifications.delay(user.id, 'new_comment',
        u'Neuer Kommentar zum Artikel „%s” ' % data.get('article_subject'),
        data,
        filter={'content_type': ctype(Article), 'object_id': data.get('article_id')})
