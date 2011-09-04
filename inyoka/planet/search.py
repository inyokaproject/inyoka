#-*- coding: utf-8 -*-
from pyes import TermFilter
from inyoka.planet.models import Entry
from inyoka.utils.search import search, DocumentType, Index
from inyoka.utils.urls import url_for


class BlogEntryDocumentType(DocumentType):
    name = 'blog_entry'
    model = Entry

    @classmethod
    def get_filter(cls, user):
        return TermFilter('hidden', False)

    @classmethod
    def serialize(cls, entry, extra):
        return {'title': entry.title,
                'user': entry.blog.name,
                'user_url': entry.blog.blog_url,
                'date': entry.pub_date,
                'url': url_for(entry),
                'blog': entry.blog.name,
                'blog_url': url_for(entry.blog),
                'text': entry.simplified_text,
                'hidden': entry.hidden}

    @classmethod
    def get_objects(cls, docids):
        return Entry.objects.select_related('blog') \
                    .filter(id__in=docids).all()

    @classmethod
    def get_doc_ids(cls):
        ids = Entry.objects.values_list('id', flat=True)
        for id in ids:
            yield id


class PlanetIndex(Index):
    name = 'planet'
    types = [BlogEntryDocumentType]


search.register(PlanetIndex)
