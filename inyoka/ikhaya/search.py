#-*- coding: utf-8 -*-
from datetime import datetime
from pyes import TermFilter, NotFilter, TypeFilter, ANDFilter, \
    RangeFilter
from inyoka.ikhaya.models import Article
from inyoka.utils.search import search, Index, DocumentType
from inyoka.utils.urls import url_for


class ArticleDocumentType(DocumentType):
    name = 'article'
    model = Article

    mapping = {'properties': {
        'pk': {'type': 'integer', 'store': 'yes'},
        'title': {'type': 'string', 'store': 'yes', 'boost': 2.0},
        'author': {'type': 'string', 'store': 'yes'},
        'date': {'type': 'date', 'store': 'yes'},
        'intro': {'type': 'string', 'store': 'yes'},
        'text': {'type': 'string', 'store': 'yes'},
        'category': {'type': 'string', 'store': 'yes'}
    }}

    @classmethod
    def get_filter(cls, user):
        now = datetime.utcnow()
        if not user.can('article_read'):
            return NotFilter(TypeFilter('article'))
        return ANDFilter((TermFilter('hidden', False),
                          RangeFilter('date', {'from': now, 'gte': True})))

    @classmethod
    def serialize(cls, article, extra):
        return {'pk': article.pk,
                'title': article.subject,
                'author': article.author.username,
                'author_url': url_for(article.author),
                'date': article.pub_datetime,
                'hidden': article.hidden,
                'category': article.category.slug,
                'url': url_for(article),
                'category_url': url_for(article.category),
                'intro': article.simplified_intro,
                'text': article.simplified_text}

    @classmethod
    def get_objects(cls, docids):
        related = ('author', 'category')
        return Article.objects.select_related(*related) \
                      .filter(id__in=docids).all()

    @classmethod
    def get_doc_ids(cls):
        ids = Article.objects.values_list('id', flat=True).all()
        for id in ids:
            yield id


class IkhayaIndex(Index):
    name = 'ikhaya'
    types = [ArticleDocumentType]


search.register(IkhayaIndex)
