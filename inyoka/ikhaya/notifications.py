# -*- coding: utf-8 -*-
"""
    inyoka.wiki.notifications
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Utilities for wiki notifications.

    :copyright: (c) 2007-2013 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from django.utils.translation import ugettext
from inyoka.utils import ctype
from inyoka.utils.notification import queue_notifications


def send_new_suggestion_notifications(user, suggestion):
    from inyoka.ikhaya.models import Suggestion
    data={'suggestion_author': suggestion.author.username,
          'suggestion_title': suggestion.title,
          'suggestion_url': suggestion.get_absolute_url()}

    queue_notifications.delay(user.id, 'new_suggestion',
        ugettext(u'New article suggestion “%(suggestion)s”') % {
            'suggestion': data.get('suggestion_title')},
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
        ugettext(u'New comment on article “%(article)s”') % {
            'article': data.get('article_subject')},
        data,
        filter={'content_type': ctype(Article),
                'object_id': data.get('article_id')})
