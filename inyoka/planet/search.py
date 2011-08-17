#-*- coding: utf-8 -*-
from inyoka.planet.models import Entry
from inyoka.utils.search import search, DocumentType, Index
from inyoka.utils.urls import url_for


class BlogEntryDocumentType(DocumentType):
    name = 'blog_entry'
    model = Entry

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


class PlanetIndex(Index):
    name = 'planet'
    types = [BlogEntryDocumentType]


search.register(PlanetIndex)
