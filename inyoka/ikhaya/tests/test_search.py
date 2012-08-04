#-*- coding: utf-8 -*-
import time
from datetime import datetime
from pyes.exceptions import ElasticSearchException
from inyoka.ikhaya.models import Article, Category
from inyoka.portal.user import User
from inyoka.utils.test import SearchTestCase


class IkhayaSearchTest(SearchTestCase):
    fixtures = ['base.json']

    def test_ikhaya_index(self):
        article = Article.objects.get(slug='well-this-is-some-article')
        self.search.store('ikhaya', 'article', article)
        self.flush_indices('ikhaya')
        results = self.search.search('some article')
        self.assertEqual('Some intro', results.hits[0].source.intro.strip())
