#-*- coding: utf-8 -*-
from django.test import TestCase

from inyoka.wiki.models import Page
from inyoka.markup import parse, RenderContext


class TestMacros(TestCase):

    def test_missing_link_in_picture_ticket_635(self):
        page = Page(name='Something')
        parse("[[Bild(Bildname, 1)]]").render(RenderContext(wiki_page=page),
                                              format='html')

    def test_toc_indention_ticket_688(self):
        node = parse("""[[Inhaltsverzeichnis(10)]]
= Stufe 1 (1) =
text
== Stufe 2 (1) ==
text
=== Stufe 3 (1) ===
text
==== Stufe 4 (1) ====
text
== Stufe 2 (5) ==
text""")
        html = node.render(RenderContext(), format='html')
        new_html = """<ol class="arabic"><li><a href="#Stufe-1-1" class="crosslink">Stufe 1 (1)
</a><ol class="arabic"><li><a href="#Stufe-2-1" class="crosslink">Stufe 2 (1)
</a><ol class="arabic"><li><a href="#Stufe-3-1" class="crosslink">Stufe 3 (1)
</a><ol class="arabic"><li><a href="#Stufe-4-1" class="crosslink">Stufe 4 (1)
</a></li></ol></li></ol></li><li><a href="#Stufe-2-5" class="crosslink">Stufe 2 (5)
</a></li></ol></li></ol>"""
        old_html = """<ol class="arabic"><li><a href="#Stufe-1-1" class="crosslink">Stufe 1 (1)
</a><ol class="arabic"><li><a href="#Stufe-2-1" class="crosslink">Stufe 2 (1)
</a><ol class="arabic"><li><a href="#Stufe-3-1" class="crosslink">Stufe 3 (1)
</a><ol class="arabic"><li><a href="#Stufe-4-1" class="crosslink">Stufe 4 (1)
</a></li></ol></li><li><a href="#Stufe-2-5" class="crosslink">Stufe 2 (5)
</a></li></ol></li></ol></li></ol>"""
        self.assertTrue(new_html in html)
        self.assertTrue(old_html not in html)
