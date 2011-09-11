#-*- coding: utf-8 -*-
import time
from datetime import datetime
from inyoka.testing import SearchTestCase
from pyes.exceptions import ElasticSearchException
from inyoka.ikhaya.models import Article, Category
from inyoka.portal.user import User


class IkhayaSearchTest(SearchTestCase):
    fixtures = ['base.json']

    def test_ikhaya_index(self):
        article = Article.objects.get(slug='well-this-is-some-article')
        self.search.store('ikhaya', 'article', article)
        time.sleep(1)
        results = self.search.search('some article')
        self.assertEqual('Some intro', results.hits[0].source.intro.strip())
