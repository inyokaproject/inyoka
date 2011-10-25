#-*- coding: utf-8 -*-
from django.test import TestCase
from inyoka.wiki.models import Page
from inyoka.wiki.parser import parse, RenderContext


class TestMacros(TestCase):

    def test_missing_link_in_picture_ticket_635(self):
        page = Page(name='Something')
        parse("[[Bild(Bildname, 1)]]").render(RenderContext(wiki_page=page),
                                              format='html')
