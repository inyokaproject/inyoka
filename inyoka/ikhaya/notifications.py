# -*- coding: utf-8 -*-
"""
    inyoka.wiki.notifications
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Utilities for wiki notifications.

    :copyright: (c) 2007-2023 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.utils.translation import ugettext

from inyoka.utils import ctype
from inyoka.utils.notification import queue_notifications


def send_new_suggestion_notifications(user, suggestion):
    from inyoka.ikhaya.models import Suggestion
    suggestion = Suggestion.objects.get(id=suggestion)
    data = {'suggestion_author': suggestion.author.username,
          'suggestion_title': suggestion.title,
          'suggestion_url': suggestion.get_absolute_url()}

    queue_notifications.delay(user, 'new_suggestion',
        ugettext('New article suggestion “%(suggestion)s”') % {
            'suggestion': data.get('suggestion_title')},
        data,
        filter={'content_type_id': ctype(Suggestion).pk})


def send_comment_notifications(user, comment, article):
    from inyoka.ikhaya.models import Article, Comment
    article = Article.objects.get(id=article)
    comment = Comment.objects.get(id=comment)
    data = {'article_id': article.id,
          'article_subject': article.subject,
          'article_unsubscribe': article.get_absolute_url('unsubscribe'),
          'comment_author': comment.author.username,
          'comment_url': comment.get_absolute_url()}

    queue_notifications.delay(user, 'new_comment',
        ugettext('New comment on article “%(article)s”') % {
            'article': data.get('article_subject')},
        data,
        filter={'content_type_id': ctype(Article).pk,
                'object_id': data.get('article_id')})
