#-*- coding: utf-8 -*-
import time
from datetime import datetime
from inyoka.testing import SearchTestCase
from pyes.exceptions import ElasticSearchException
from inyoka.ikhaya.models import Article, Category
from inyoka.portal.user import User


class IkhayaSearchTest(SearchTestCase):

    def test_ikhaya_index(self):
        user = User.objects.create_user('test', 'test@bla.com')
        category = Category.objects.create(name='Testcategory')
        now = datetime.utcnow()
        article = Article(author=user, subject=u'Some test article',
                          intro='Yea!', text=u'And more testing',
                          public=True,
                          pub_date=now.date(),
                          pub_time=now.time(),
                          category=category)
        article.save()
        self.search.store('ikhaya', 'article', article)
        time.sleep(1)
        results = self.search.search('test article')
        self.assertEqual('Yea!', results.hits[0].source.intro.strip())
