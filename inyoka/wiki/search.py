# -*- coding: utf-8 -*-
"""
    inyoka.wiki.search
    ~~~~~~~~~~~~~~~~~~

    Search interfaces for the wiki.

    :copyright: (c) 2007-2015 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from inyoka.portal.user import User
from inyoka.utils.search import search, SearchAdapter
from inyoka.utils.urls import href, url_for
from inyoka.wiki.acl import PRIV_READ, MultiPrivilegeTest
from inyoka.wiki.models import Page, Revision


class WikiSearchAuthDecider(object):
    """Decides whetever a user can display a search result or not."""

    def __init__(self, user):
        self.test = MultiPrivilegeTest(user)

    def __call__(self, page_name):
        return self.test.has_privilege(page_name, PRIV_READ)


class WikiSearchAdapter(SearchAdapter):
    type_id = 'w'
    auth_decider = WikiSearchAuthDecider

    def get_objects(self, docids):
        related = ('page__name', 'text__value')
        return Revision.objects.select_related(*related) \
                       .filter(id__in=docids).all()

    def extract_data(self, rev):
        user = rev.user or User.ANONYMOUS_USER
        return {'title': rev.page.title,
                'user': user,
                'date': rev.change_date,
                'url': url_for(rev.page),
                'component': u'Wiki',
                'group': u'Wiki',
                'group_url': href('wiki'),
                'highlight': True,
                'text': rev.rendered_text,
                'hidden': rev.deleted,
                'user_url': url_for(user)}

    def recv(self, page_id):
        rev = Revision.objects.select_related('page', 'user', 'text') \
                .filter(page__id=page_id).latest()
        return self.extract_data(rev)

    def recv_multi(self, page_ids):
        revlist = list(Page.objects.values_list('last_rev_id', flat=True)
                                   .filter(id__in=page_ids).order_by())

        revisions = Revision.objects.select_related('page', 'user', 'text') \
                            .filter(id__in=revlist)

        return [self.extract_data(rev) for rev in revisions]

    def store_object(self, revision, connection=None):
        search.store(connection,
                     component='w',
                     uid=revision.page.id,
                     title=revision.page.name,
                     user=revision.user_id,
                     date=revision.change_date,
                     auth=revision.page.name,
                     text=revision.text.value,
                     category=revision.attachment_id and '__attachment__' or None)

    def get_doc_ids(self):
        pages = Page.objects.values_list('last_rev__id', flat=True).order_by('last_rev__id')
        for row in pages:
            yield row


search.register(WikiSearchAdapter())
