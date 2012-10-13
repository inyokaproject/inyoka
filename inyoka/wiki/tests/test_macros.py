#-*- coding: utf-8 -*-
from django.test import TestClient
from inyoka.markup import macros


class TestWikiMacros(TestClient):

    def test_recent_changes_registered(self):
        gm = macros.get_macro
        self.assertEqual(gm('RecentChanges').__class__.__name__,
                         'RecentChanges')
        self.assertEqual(gm(u'LetzteÄnderungen').__class__.__name__,
                         'RecentChanges')
