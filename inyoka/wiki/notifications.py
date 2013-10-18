# -*- coding: utf-8 -*-
"""
    inyoka.wiki.notifications
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Utilities for wiki notifications.

    :copyright: (c) 2007-2013 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from django.conf import settings
from django.utils.translation import ugettext as _

from inyoka.utils import ctype
from inyoka.utils.urls import href
from inyoka.utils.notification import queue_notifications


def send_edit_notifications(user, rev, old_rev):
    from inyoka.wiki.models import Page
    # notify about new answer in topic for topic-subscriptions

    anonymous = settings.INYOKA_ANONYMOUS_USER

    old_rev_id = old_rev.id
    page = rev.page
    data = {
        'changes_link': href('wiki', page.name, action='diff', rev=old_rev_id),
        'diff_link': href('wiki', page.name, action='diff', rev=old_rev_id, new_rev=rev.id),
        'page_title': page.title,
        'rev_note': rev.note,
        'rev_username': rev.user.username if rev.user else anonymous,
        'unsubscribe_link': href('wiki', page.name, action='unsubscribe'),
    }

    queue_notifications.delay(user.id, 'page_edited',
        _(u'The page “%(name)s” was changed') % {'name': data.get('page_title')},
        data,
        filter={'content_type': ctype(Page), 'object_id': data.get('page_id')})
