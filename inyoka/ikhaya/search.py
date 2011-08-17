#-*- coding: utf-8 -*-
from datetime import datetime
from pyes import TermsFilter, ORFilter, TermFilter
from inyoka.ikhaya.models import Article
from inyoka.utils.search import search, Index, DocumentType
from inyoka.utils.urls import url_for, href


class ArticleSearchAuthDecider(object):
    """Decides whether a user can display a search result or not."""

    def __init__(self, user):
        self.now = datetime.utcnow()
        self.priv = user.can('article_read')

    def __call__(self, auth):
        if not isinstance(auth[1], datetime):
            # this is a workaround for old data in search-index.
            auth = list(auth)
            auth[1] = datetime(auth[1].year, auth[1].month, auth[1].day)
            auth = tuple(auth)
        return self.priv or ((not auth[0]) and auth[1] <= self.now)


class ArticleDocumentType(DocumentType):
    name = 'article'
    model = Article

    @classmethod
    def get_filter(cls, user):
        now = datetime.utcnow()
        priv = user.can('article_read')
        if not user.can('article_read'):
            return NotFilter(TypeFilter('article'))
        return ANDFilter((TermFilter('hidden', False),
                          RangeFilter('date', {'from': now, 'gte': True})))

    @classmethod
    def serialize(cls, article, extra):
        return {'pk': article.pk,
                'title': article.subject,
                'user': article.author.username,
                'date': article.pub_datetime,
                'hidden': article.hidden,
                'category': article.category.slug,
                'url': url_for(article),
                'category_url': url_for(article.category),
                'intro': article.simplified_intro,
                'text': article.simplified_text,
                'user_url': url_for(article.author)}


class IkhayaIndex(Index):
    name = 'ikhaya'
    types = [ArticleDocumentType]


search.register(IkhayaIndex)
