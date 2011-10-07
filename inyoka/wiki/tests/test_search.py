#-*- coding: utf-8 -*-
import time
from inyoka.testing import SearchTestCase
from pyes.exceptions import ElasticSearchException
from inyoka.wiki.models import Page


class WikiSearchTest(SearchTestCase):

    def test_wiki_index(self):
        page = Page.objects.create('SearchTest', 'Some Search Text',
                                   note=u'Created for unittest purposes')
        self.search.store('wiki', 'page', page)
        self.flush_indices('wiki')
        results = self.search.search('Search Text')
        self.assertEqual('SearchTest', results.hits[0].source.title)
