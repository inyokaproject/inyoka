"""
    inyoka.wiki.notifications
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Utilities for wiki notifications.

    :copyright: (c) 2007-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.conf import settings
from django.utils.translation import gettext as _

from inyoka.utils import ctype
from inyoka.utils.notification import queue_notifications
from inyoka.utils.urls import url_for


def send_edit_notifications(user, rev, old_rev):
    from inyoka.wiki.models import Page
    # notify about new answer in topic for topic-subscriptions

    anonymous = settings.ANONYMOUS_USER_NAME

    data = {
        'page_name': rev.page.name,
        'page_title': rev.page.title,
        'rev_note': rev.note,
        'rev_username': rev.user.username if rev.user else anonymous,
        'unsubscribe_url': url_for(rev.page, action='unsubscribe'),
        'diff_url': url_for(rev.page, action='diff', revision=old_rev.id,
                            new_revision=rev.id),
        'changes_url': url_for(rev.page, action='diff', revision=old_rev.id),
        'page_url': rev.page.get_absolute_url(),
        }

    subject = _('The page “{name}” was changed').format(name=data.get('page_title'))
    filter = {'content_type_id': ctype(Page).pk, 'object_id': rev.page.id}

    queue_notifications.delay(user.id, 'page_edited', subject, data,
                              filter=filter)
