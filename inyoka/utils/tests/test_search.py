#-*- coding: utf-8 -*-
"""
    inyoka.utils.tests.test_search
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2012 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.utils.test import SearchTestCase
from inyoka.utils.tests.models import Stanza



class TestSearchImplementation(SearchTestCase):

    def test_store(self):
        m = Stanza(data='something different')
        m.save()
        self.search.store('stanza', 'stanza', m)
        self.flush_indices('stanza')
        results = self.search.search('different')
        self.assertEqual('something different', results.hits[0].source.data)

    def test_autodelete(self):
        m = Stanza(data='something different')
        m.save()
        self.search.store('stanza', 'stanza', m)
        self.flush_indices('stanza')
        results = self.search.search('different')
        self.assertEqual('something different', results.hits[0].source.data)
        m = Stanza.objects.get(data='something different')
        m.delete()
        self.flush_indices('stanza')
        self.assertEqual(self.search.search('different').hits, [])

    def test_autoupdate(self):
        m = Stanza(data='something different')
        m.save()
        self.search.store('stanza', 'stanza', m)
        self.flush_indices('stanza')
        results = self.search.search('different')
        self.assertEqual('something different', results.hits[0].source.data)
        m = Stanza.objects.get(data='something different')
        m.data = 'updated'
        m.save()
        self.flush_indices('stanza')
        self.assertEqual(self.search.search('different').hits, [])
        results = self.search.search('updated').hits
        self.assertEqual(results[0].source.data, 'updated')
