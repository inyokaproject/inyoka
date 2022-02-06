# -*- coding: utf-8 -*-
"""
    tests.apps.wiki.test_macros
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test wiki macros.

    :copyright: (c) 2012-2022 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from inyoka.markup import macros
from inyoka.markup.base import RenderContext, parse
from inyoka.utils.test import TestCase
from inyoka.utils.urls import href
from inyoka.wiki.models import Page


class TestWikiMacros(TestCase):
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

    def test_taglist(self):
        page = Page(name='Something')
        html = parse("""[[TagListe("Ubuntu Touch")]]""").render(
            RenderContext(wiki_page=page, application='wiki'),
            format='html'
        )

        needle = '<div><h3 id="Pages-with-tag-Ubuntu-Touch" class="head">Pages with tag “Ubuntu Touch”' \
                 '<a href="#Pages-with-tag-Ubuntu-Touch" class="headerlink">¶</a></h3><ul class="taglist"></ul></div>'
        self.assertInHTML(needle, html)
