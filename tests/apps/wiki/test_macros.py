#-*- coding: utf-8 -*-
"""
    tests.apps.wiki.test_macros
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test wiki macros.

    :copyright: (c) 2012-2015 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import unittest
from inyoka.utils.test import TestCase

from inyoka.markup import macros, RenderContext
from inyoka.utils.urls import href
from inyoka.wiki.models import Page


class TestWikiMacros(TestCase):

    def test_recent_changes_registered(self):
        gm = macros.get_macro
        self.assertEqual(gm('RecentChanges', (), {}).__class__.__name__,
                         'RecentChanges')
        self.assertEqual(gm(u'LetzteÄnderungen', (), {}).__class__.__name__,
                         'RecentChanges')

    def test_attachment_macro(self):
        gm = macros.get_macro
        ct = RenderContext(wiki_page=Page(name='AttachmentTest'))
        at1 = gm('Attachment', ('http://somesite.com', 'sometext'), {})
        link = at1.build_node(ct, 'html')
        self.assertEqual(link.href, 'http://somesite.com')
        self.assertEqual(link.text, 'sometext')

        at1 = gm('Attachment', ('internal_page', 'sometext'), {})
        link = at1.build_node(ct, 'html')
        self.assertEqual(link.href, href('wiki', '_attachment',
                            target='AttachmentTest/internal_page'))
        self.assertEqual(link.text, 'sometext')

    @unittest.skip("Not implemented yet.")
    def test_tag_cloud(self):
        pass
