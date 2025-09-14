"""
    tests.apps.wiki.test_macros
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test wiki macros.

    :copyright: (c) 2012-2025 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.test import override_settings

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

    def test_filterbymetadata__no_result(self):
        page = Page(name='Something')
        html = parse("""[[FilterByMetaData("X-Link: foo")]]""").render(
            RenderContext(wiki_page=page, application='wiki'),
            format='html'
        )

        needle = '<div class="error"><strong>No result</strong><p>The metadata filter has found no results. Query: X-Link: foo</p></div>'
        self.assertInHTML(needle, html)

    def test_filterbymetadata__simple_query(self):
        Page.objects.create('foo', 'some text')
        Page.objects.create('bar', 'test [:foo:content]')

        page = Page(name='Something')
        html = parse("""[[FilterByMetaData("X-Link: foo")]]""").render(
            RenderContext(wiki_page=page, application='wiki'),
            format='html'
        )

        needle = '<ul><li><a href="http://wiki.ubuntuusers.local:8080/bar/" class="internal">bar</a></li></ul>'
        self.assertInHTML(needle, html)

    @override_settings(WIKI_PRIVILEGED_PAGES=['internal', 'Trash'])
    def test_filterbymetadata__exclude_privileged_pages(self):
        """
        Pages starting with internal and Trash should not be displayed, even if they
        match the query.
        """
        Page.objects.create('foo', 'some text')
        Page.objects.create('bar', 'test [:foo:content]')
        Page.objects.create('internal/bar', 'test [:foo:link]')
        Page.objects.create('Trash/old_bar', 'test [:foo:link]')

        page = Page(name='Something')
        html = parse("""[[FilterByMetaData("X-Link: foo")]]""").render(
            RenderContext(wiki_page=page, application='wiki'),
            format='html'
        )

        needle = '<ul><li><a href="http://wiki.ubuntuusers.local:8080/bar/" class="internal">bar</a></li></ul>'
        self.assertInHTML(needle, html)

    def test_filterbymetadata__invalid_filter_syntax(self):
        """Two `:` (`::`) in filter query is invalid syntax."""
        page = Page(name='Something')
        html = parse("""[[FilterByMetaData("X-Link:: foo")]]""").render(
            RenderContext(wiki_page=page, application='wiki'),
            format='html'
        )

        needle = '<div class="error"><strong>No result</strong><p>Invalid filter syntax. Query: X-Link:: foo</p></div>'
        self.assertInHTML(needle, html)

    def test_filterbymetadata__invalid_key(self):
        page = Page(name='Something')
        html = parse("""[[FilterByMetaData("barbazb: foo")]]""").render(
            RenderContext(wiki_page=page, application='wiki'),
            format='html'
        )

        needle = '<div class="error"><strong>No result</strong><p>Invalid filter key barbazb. Query: barbazb: foo</p></div>'
        self.assertInHTML(needle, html)

    def test_filterbymetadata__invalid_key_script(self):
        """Test for a simple XSS attempt"""
        page = Page(name='Something')
        html = parse("""[[FilterByMetaData("<script>echo(a)</script>: <script>echo(a)</script>")]]""").render(
            RenderContext(wiki_page=page, application='wiki'),
            format='html'
        )

        needle = '<div class="error"><strong>No result</strong><p>Invalid filter key &lt;script&gt;echo(a)&lt;/script&gt;. Query: &lt;script&gt;echo(a)&lt;/script&gt;: &lt;script&gt;echo(a)&lt;/script&gt;</p></div>'
        self.assertInHTML(needle, html)

    def test_filterbymetadata__not(self):
        Page.objects.create('foo', 'some text')
        Page.objects.create('baz', 'another page')
        Page.objects.create('bar', 'test [:foo:content]')
        Page.objects.create('linkbaz', 'links [:baz:]')

        page = Page(name='Something')
        html = parse("""[[FilterByMetaData("X-Link: NOT foo")]]""").render(
            RenderContext(wiki_page=page, application='wiki'),
            format='html'
        )

        needle = '''<ul>
        <li><a href="http://wiki.ubuntuusers.local:8080/Wiki/Index/" class="internal">Wiki/Index</a></li>
        <li><a href="http://wiki.ubuntuusers.local:8080/baz/" class="internal">baz</a></li>
        <li><a href="http://wiki.ubuntuusers.local:8080/foo/" class="internal">foo</a></li>
        <li><a href="http://wiki.ubuntuusers.local:8080/linkbaz/" class="internal">linkbaz</a></li>
        </ul>'''
        self.assertInHTML(needle, html)

    def test_filterbymetadata__not__multiple_links_on_page(self):
        """
        `baz` and `linkbaz` have multiple links. If one of the links points to `foo`,
        the page is excluded.
        """
        Page.objects.create('foo', 'some text')
        Page.objects.create('baz', '[:foo:content] [:bar:another page]')
        Page.objects.create('bar', 'test [:foo:content]')
        Page.objects.create('linkbaz', 'links [:baz:] [:bar:]')

        page = Page(name='Something')
        html = parse("""[[FilterByMetaData("X-Link: NOT foo")]]""").render(
            RenderContext(wiki_page=page, application='wiki'),
            format='html'
        )

        needle = '''<ul>
        <li><a href="http://wiki.ubuntuusers.local:8080/Wiki/Index/" class="internal">Wiki/Index</a></li>
        <li><a href="http://wiki.ubuntuusers.local:8080/foo/" class="internal">foo</a></li>
        <li><a href="http://wiki.ubuntuusers.local:8080/linkbaz/" class="internal">linkbaz</a></li>
        </ul>'''
        self.assertInHTML(needle, html)

    def  test_filterbymetadata__tag(self):
        Page.objects.create('foo', 'some text\n# tag: foo')
        Page.objects.create('baz', 'another page\n# tag: baz')

        page = Page(name='Something')
        html = parse("""[[FilterByMetaData("tag: foo")]]""").render(
            RenderContext(wiki_page=page, application='wiki'),
            format='html'
        )

        needle = '<ul><li><a href="http://wiki.ubuntuusers.local:8080/foo/" class="internal">foo</a></li></ul>'
        self.assertInHTML(needle, html)

    def test_filterbymetadata__xlink_and_xlink__no_result(self):
        Page.objects.create('foo', 'some text')
        Page.objects.create('bar', 'test [:foo:content]')
        Page.objects.create('intbar', 'test [:foo:link]')
        Page.objects.create('old_bar', 'test [:bar:link]')

        page = Page(name='Something')
        html = parse("""[[FilterByMetaData("X-Link: foo; X-Link: bar")]]""").render(
            RenderContext(wiki_page=page, application='wiki'),
            format='html'
        )

        needle = '''<div class="error"><strong>No result</strong>
        <p>The metadata filter has found no results. Query: X-Link: foo; X-Link: bar</p>
        </div>
        '''
        self.assertInHTML(needle, html)

    def test_filterbymetadata__xlink_two_values(self):
        Page.objects.create('foo', 'some text')
        Page.objects.create('bar', 'test [:foo:content]')
        Page.objects.create('intbar', 'test [:foo:link]')
        Page.objects.create('old_bar', 'test [:bar:link]')

        page = Page(name='Something')
        html = parse("""[[FilterByMetaData("X-Link: foo,bar")]]""").render(
            RenderContext(wiki_page=page, application='wiki'),
            format='html'
        )

        needle = '''<ul>
        <li><a href="http://wiki.ubuntuusers.local:8080/bar/" class="internal">bar</a></li>
        <li><a href="http://wiki.ubuntuusers.local:8080/intbar/" class="internal">intbar</a></li>
        <li><a href="http://wiki.ubuntuusers.local:8080/old_bar/" class="internal">old bar</a></li>
        </ul>
        '''
        self.assertInHTML(needle, html)

    def test_filterbymetadata__xlink_and_tag(self):
        Page.objects.create('foo', 'some text')
        Page.objects.create('bar', 'test [:foo:content]\n#tag: gras')
        Page.objects.create('intbar', 'test [:foo:link]\n#tag: new')
        Page.objects.create('old_bar', 'test [:bar:link]\n#tag: old')
        Page.objects.create('odd_bar', 'test [:bar:link]\n#tag: gras')

        page = Page(name='Something')
        html = parse("""[[FilterByMetaData("X-Link: foo; tag: gras")]]""").render(
            RenderContext(wiki_page=page, application='wiki'),
            format='html'
        )

        needle = '''<ul>
        <li><a href="http://wiki.ubuntuusers.local:8080/bar/" class="internal">bar</a></li>
        </ul>
        '''
        self.assertInHTML(needle, html)

    def test_filterbymetadata__not_xlink_and_tag(self):
        Page.objects.create('foo', 'some text\n#tag: gras')
        Page.objects.create('bar', 'test [:foo:content]\n#tag: gras')
        Page.objects.create('intbar', 'test [:foo:link]\n#tag: new')
        Page.objects.create('old_bar', 'test [:bar:link]\n#tag: old')
        Page.objects.create('odd_bar', 'test [:bar:link]\n#tag: gras')

        page = Page(name='Something')
        with self.assertNumQueries(1):
            html = parse("""[[FilterByMetaData("X-Link: NOT bar; tag: gras")]]""").render(
                RenderContext(wiki_page=page, application='wiki'),
                format='html'
            )

        needle = '''<ul>
        <li><a href="http://wiki.ubuntuusers.local:8080/bar/" class="internal">bar</a></li>
        <li><a href="http://wiki.ubuntuusers.local:8080/foo/" class="internal">foo</a></li>
        </ul>
        '''
        self.assertInHTML(needle, html)

    def test_filterbymetadata__not_xlink__multiple_links_in_page(self):
        Page.objects.create('foo', 'some text\n#tag: gras')
        Page.objects.create('odd_bar', 'test [:bar:link] [:gras:link]\n#tag: gras')

        page = Page(name='Something')
        with self.assertNumQueries(1):
            html = parse("""[[FilterByMetaData("X-Link: NOT bar")]]""").render(
                RenderContext(wiki_page=page, application='wiki'),
                format='html'
            )

        needle = '''<ul>
            <li><a href="http://wiki.ubuntuusers.local:8080/Wiki/Index/" class="internal">Wiki/Index</a></li>
            <li><a href="http://wiki.ubuntuusers.local:8080/foo/" class="internal">foo</a></li>
        </ul>
        '''
        self.assertInHTML(needle, html)

    def test_filterbymetadata__not_xlink_and_multiple_tag(self):
        Page.objects.create('foo', 'some text\n#tag: gras')
        Page.objects.create('bar', 'test [:foo:content]\n#tag: gras')
        Page.objects.create('intbar', 'test [:foo:link]\n#tag: new')
        Page.objects.create('old_bar', 'test [:bar:link]\n#tag: gras')
        Page.objects.create('odd_bar', 'test [:bar:link]\n#tag: gras')
        Page.objects.create('gras', 'test [:old_bar:link] \n#tag: baz')

        page = Page(name='Something')
        with self.assertNumQueries(1):
            html = parse("""[[FilterByMetaData("X-Link: NOT bar; tag: gras,baz")]]""").render(
                RenderContext(wiki_page=page, application='wiki'),
                format='html'
            )

        needle = '''<ul>
            <li><a href="http://wiki.ubuntuusers.local:8080/bar/" class="internal">bar</a></li>
            <li><a href="http://wiki.ubuntuusers.local:8080/foo/" class="internal">foo</a></li>
            <li><a href="http://wiki.ubuntuusers.local:8080/gras/" class="internal">gras</a></li>
        </ul>
        '''
        self.assertInHTML(needle, html)

    def test_filterbymetadata__tag_and_multiple_link(self):
        Page.objects.create('foo', 'some text\n#tag: gras')
        Page.objects.create('bar', 'test [:foo:content]\n#tag: gras')
        Page.objects.create('intbar', 'test [:foo:link]\n#tag: new')
        Page.objects.create('old_bar', 'test [:bar:link]\n#tag: old')
        Page.objects.create('odd_bar', 'test [:bar:link]\n#tag: gras')

        page = Page(name='Something')
        with self.assertNumQueries(1):
            html = parse("""[[FilterByMetaData("tag: gras; X-Link: bar,foo")]]""").render(
                RenderContext(wiki_page=page, application='wiki'),
                format='html'
            )

        needle = '''<ul>
        <li><a href="http://wiki.ubuntuusers.local:8080/bar/" class="internal">bar</a></li>
        <li><a href="http://wiki.ubuntuusers.local:8080/odd_bar/" class="internal">odd bar</a></li>
        </ul>
        '''
        self.assertInHTML(needle, html)

    def test_filterbymetadata__invalid_not__two_values(self):
        Page.objects.create('foo', 'some text\n#tag: gras')
        Page.objects.create('bar', 'test [:foo:content]\n#tag: gras')
        Page.objects.create('intbar', 'test [:foo:link]\n#tag: new')
        Page.objects.create('old_bar', 'test [:bar:link]\n#tag: old')
        Page.objects.create('odd_bar', 'test [:bar:link]\n#tag: gras')

        page = Page(name='Something')
        html = parse("""[[FilterByMetaData("tag: gras; X-Link: NOT bar,foo")]]""").render(
            RenderContext(wiki_page=page, application='wiki'),
            format='html'
        )

        needle = '''<div class="error">
        <strong>No result</strong><p>Invalid filter syntax. Query: tag: gras; X-Link: NOT bar,foo</p>
        </div>
        '''
        self.assertInHTML(needle, html)

    def test_filterbymetadata__multiple_tags_on_pages(self):
        Page.objects.create('foo', 'some text\n#tag: gras,baz')
        Page.objects.create('bar', 'test [:foo:content]\n#tag: gras,bar')
        Page.objects.create('bar2', 'test [:foo:content]\n#tag: gras,bar')
        Page.objects.create('intbar', 'test [:foo:link]\n#tag: new,bar')
        Page.objects.create('old_bar', 'test [:bar:link]\n#tag: old,bar')
        Page.objects.create('odd_bar', 'test [:bar:link]\n#tag: gras,bar')

        page = Page(name='Something')
        with self.assertNumQueries(1):
            html = parse("""[[FilterByMetaData("X-Link: NOT bar; tag: gras")]]""").render(
                RenderContext(wiki_page=page, application='wiki'),
                format='html'
            )

        needle = '''<ul>
        <li><a href="http://wiki.ubuntuusers.local:8080/bar/" class="internal">bar</a></li>
        <li><a href="http://wiki.ubuntuusers.local:8080/bar2/" class="internal">bar2</a></li>
        <li><a href="http://wiki.ubuntuusers.local:8080/foo/" class="internal">foo</a></li>
        </ul>
        '''
        self.assertInHTML(needle, html)

    def test_filterbymetadata__not_at_end(self):
        Page.objects.create('foo', 'some text\n#tag: gras,baz')
        Page.objects.create('bar', 'test [:foo:content]\n#tag: gras,bar')
        Page.objects.create('bar2', 'test [:foo:content]\n#tag: gras,bar')
        Page.objects.create('intbar', 'test [:foo:link]\n#tag: new,bar')
        Page.objects.create('old_bar', 'test [:bar:link]\n#tag: old,bar')
        Page.objects.create('odd_bar', 'test [:bar:link]\n#tag: gras,bar')

        page = Page(name='Something')

        html = parse("""[[FilterByMetaData("tag: gras; X-Link: NOT bar")]]""").render(
            RenderContext(wiki_page=page, application='wiki'),
            format='html'
        )

        needle = '''<ul>
        <li><a href="http://wiki.ubuntuusers.local:8080/bar/" class="internal">bar</a></li>
        <li><a href="http://wiki.ubuntuusers.local:8080/bar2/" class="internal">bar2</a></li>
        <li><a href="http://wiki.ubuntuusers.local:8080/foo/" class="internal">foo</a></li>
        </ul>
        '''
        self.assertInHTML(needle, html)

    def test_filterbymetadata__not_at_start_and_end(self):
        Page.objects.create('foo', 'some text\n#tag: gras,baz')
        Page.objects.create('bar', 'test [:foo:content]\n#tag: gras,bar')
        Page.objects.create('bar2', 'test [:foo:content]\n#tag: gras,bar')
        Page.objects.create('intbar', 'test [:foo:link]\n#tag: new,bar')
        Page.objects.create('old_bar', 'test [:bar:link]\n#tag: old,bar')
        Page.objects.create('odd_bar', 'test [:bar:link]\n#tag: gras,bar')

        page = Page(name='Something')
        html = parse("""[[FilterByMetaData("tag: NOT foo; tag: gras; X-Link: NOT bar")]]""").render(
            RenderContext(wiki_page=page, application='wiki'),
            format='html'
        )

        needle = '''<ul>
        <li><a href="http://wiki.ubuntuusers.local:8080/bar/" class="internal">bar</a></li>
        <li><a href="http://wiki.ubuntuusers.local:8080/bar2/" class="internal">bar2</a></li>
        <li><a href="http://wiki.ubuntuusers.local:8080/foo/" class="internal">foo</a></li>
        </ul>
        '''
        self.assertInHTML(needle, html)

    def test_filterbymetadata__two_not(self):
        Page.objects.create('foo', 'some text\n#tag: baz')
        Page.objects.create('bar', 'test [:foo:content]\n#tag: gras')
        Page.objects.create('bar2', 'test [:foo:content]\n#tag: gras')
        Page.objects.create('intbar', 'test [:foo:link]\n#tag: new,bar')
        Page.objects.create('old_bar', 'test [:bar:link] [:foo:]\n#tag: old')
        Page.objects.create('odd_bar', 'test [:bar:link]\n#tag: gras')

        page = Page(name='Something')
        with self.assertNumQueries(1):
            html = parse("""[[FilterByMetaData("X-Link: NOT bar; tag: NOT gras")]]""").render(
                RenderContext(wiki_page=page, application='wiki'),
                format='html'
            )

        needle = '''<ul>
        <li><a href="http://wiki.ubuntuusers.local:8080/Wiki/Index/" class="internal">Wiki/Index</a></li>
        <li><a href="http://wiki.ubuntuusers.local:8080/foo/" class="internal">foo</a></li>
        <li><a href="http://wiki.ubuntuusers.local:8080/intbar/" class="internal">intbar</a></li>
        </ul>
        '''
        self.assertInHTML(needle, html)

    def test_filterbymetadata__two_not_at_start(self):
        Page.objects.create('foo', 'some text\n#tag: baz')
        Page.objects.create('bar', 'test [:foo:content]\n#tag: gras')
        Page.objects.create('bar2', 'test [:foo:content]\n#tag: gras')
        Page.objects.create('intbar', 'test [:foo:link]\n#tag: new,bar')
        Page.objects.create('old_bar', 'test [:bar:link]\n#tag: old')
        Page.objects.create('odd_bar', 'test [:bar:link]\n#tag: gras')

        page = Page(name='Something')
        with self.assertNumQueries(1):
            html = parse("""[[FilterByMetaData("X-Link: NOT bar; tag: NOT gras; X-Link: foo")]]""").render(
                RenderContext(wiki_page=page, application='wiki'),
                format='html'
            )

        needle = '''<ul>
        <li><a href="http://wiki.ubuntuusers.local:8080/intbar/" class="internal">intbar</a></li>
        </ul>
        '''
        self.assertInHTML(needle, html)
