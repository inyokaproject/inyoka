#-*- coding: utf-8 -*-
"""
    inyoka.ikhaya.search
    ~~~~~~~~~~~~~~~~~~~

    Search interfaces for ikhaya.

    :copyright: (c) 2007-2013 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from datetime import datetime
from inyoka.utils.search import SearchAdapter, search
from inyoka.utils.urls import url_for
from inyoka.ikhaya.models import Article


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


class IkhayaSearchAdapter(SearchAdapter):
    type_id = 'i'
    auth_decider = ArticleSearchAuthDecider

    def get_objects(self, docids):
        return Article.objects.select_related(depth=1) \
                      .filter(id__in=docids).all()

    def store_object(self, article, connection=None):
        search.store(connection,
            component='i',
            uid=article.id,
            title=article.subject,
            user=article.author_id,
            date=article.pub_datetime,
            auth=(article.hidden, article.pub_datetime),
            category=article.category.slug,
            text=[article.intro, article.text]
        )

    def extract_data(self, article):
        return {'title': article.subject,
                'user': article.author.username,
                'date': article.pub_datetime,
                'url': url_for(article),
                'component': u'Ikhaya',
                'group': article.category.name,
                'group_url': url_for(article.category),
                'highlight': True,
                'text': u'%s %s' % (article.simplified_intro,
                                    article.simplified_text),
                'hidden': article.hidden,
                'user_url': url_for(article.author)}

    def recv(self, docid):
        article = Article.objects.select_related(depth=1).get(id=docid)
        return self.extract_data(article)

    def recv_multi(self, docids):
        articles = Article.objects.select_related(depth=1).filter(id__in=docids)
        return [self.extract_data(article) for article in articles]

    def get_doc_ids(self):
        ids = Article.objects.values_list('id', flat=True).all()
        for id in ids:
            yield id


#: Register search adapter
search.register(IkhayaSearchAdapter())
