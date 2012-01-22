# -*- coding: utf-8 -*-
"""
    inyoka.wiki.notifications
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Utilities for wiki notifications.

    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from django.utils.translation import ugettext as _
from inyoka.utils import ctype
from inyoka.utils.notification import queue_notifications


def send_edit_notifications(user, rev, old_rev):
    from inyoka.wiki.models import Page
    # notify about new answer in topic for topic-subscriptions

    data={'old_rev_id': old_rev.id,
          'page_id': rev.page.id,
          'page_name': rev.page.name,
          'page_title': rev.page.title,
          'rev_id': rev.id,
          'rev_note': rev.note,
          'rev_username': rev.user.username if rev.user else 'Anonymous'}
    queue_notifications.delay(user.id, 'page_edited',
        _(u'The page “%(name)s” was changed') % {'name': data.get('page_title')},
        data,
        filter={'content_type': ctype(Page), 'object_id': data.get('page_id')})
