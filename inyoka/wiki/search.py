#-*- coding: utf-8 -*-
from pyes import TermsFilter, NotFilter
from inyoka.utils.search import search, Index, DocumentType
from inyoka.wiki.acl import get_all_pages_without_privilege, PRIV_READ
from inyoka.wiki.models import Page
from inyoka.portal.user import User
from inyoka.utils.urls import url_for, href


class PageDocumentType(DocumentType):
    name = 'page'
    model = Page

    mapping = {'properties': {
        'pk': {'type': 'integer', 'store': 'yes'},
        'title': {'type': 'string', 'store': 'yes', 'boost': '2.0'},
        'author': {'type': 'string', 'store': 'yes'},
        'date': {'type': 'date', 'store': 'yes'},
        'text': {'type': 'string', 'store': 'yes'},
        'blog': {'type': 'string', 'store': 'yes'}
    }}

    @classmethod
    def get_filter(cls, user):
        pages = get_all_pages_without_privilege(user, PRIV_READ)
        return ANDFilter((NotFilter(TermsFilter('title', pages)),
                          NotFilter(TermsFilter('attachment', True))))

    @classmethod
    def serialize(cls, page, extra):
        user = page.last_rev.user or User.objects.get_anonymous_user()
        return {
            'pk': page.pk,
            'title': page.title,
            'author': user.username,
            'author_url': url_for(user),
            'date': page.last_rev.change_date,
            'url': url_for(page),
            'text': page.last_rev.text.parse().text,
            'hidden': page.last_rev.deleted,
            'attachment': page.last_rev.attachment_id is not None
        }

    @classmethod
    def get_doc_ids(cls):
        pages = Page.objects.values_list('pk', flat=True).order_by('pk')
        for row in pages:
            yield row

    @classmethod
    def get_objects(cls, docids):
        related = ('last_rev__text__value')
        return Page.objects.select_related(*related) \
                           .filter(id__in=docids).all()


class WikiIndex(Index):
    name = 'wiki'
    types = [PageDocumentType]


search.register(WikiIndex)
