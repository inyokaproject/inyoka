"""
tests.apps.markup.test_html_renderer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here we test the HTML rendering.

:copyright: (c) 2013-2024 by the Inyoka Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from os import path

from django.conf import settings
from django.test import override_settings

from inyoka.markup.base import Parser, RenderContext
from inyoka.markup.transformers import DEFAULT_TRANSFORMERS, SmileyInjector
from inyoka.portal.user import User
from inyoka.utils.test import TestCase
from inyoka.utils.urls import href
from inyoka.wiki.models import Page


def render(source, transformers=None, application=None):
    """Parse source and render it to html."""
    if not transformers:
        transformers = []
    tree = Parser(source, transformers).parse()
    html = tree.render(RenderContext(application=application), 'html')
    return html


def render_smilies(source):
    return render(source, [SmileyInjector()])


class TestHtmlRenderer(TestCase):
    def test_simple_markup(self):
        """Test the simple markup."""
        html = render("''foo'', '''bar''', __baz__, ,,(foo),,, ^^(bar)^^")
        self.assertHTMLEqual(
            html,
            (
                '<em>foo</em>, '
                '<strong>bar</strong>, '
                '<span class="underline">baz</span>, '
                '<sub>foo</sub>, '
                '<sup>bar</sup>'
            ),
        )

    def test_pre(self):
        """Check if pre renders correctly."""
        self.assertHTMLEqual(
            render('{{{\n<em>blub</em>\n}}}'),
            '<pre class="notranslate">&lt;em&gt;blub&lt;/em&gt;</pre>',
        )

    def test_color(self):
        html = render(' [color=red]TEXT[/color]  [color=#ABCDEF]TEXT[/color] ')
        self.assertHTMLEqual(
            html,
            (
                '<span style="color: #ff0000">TEXT</span> <span style="color: #abcdef">TEXT</span>'
            ),
        )

    def test_color_not_existing(self):
        html = render(' [color=redfuu]TEXT[/color]')
        self.assertHTMLEqual(html, '<span style="color: #000000">TEXT</span>')

    def test_small(self):
        html = render('~-(TEXT)-~')
        self.assertHTMLEqual(html, '<small>TEXT</small>')

    def test_big(self):
        html = render('~+(TEXT)+~')
        self.assertHTMLEqual(html, '<big>TEXT</big>')

    def test_font_and_size(self):
        html = render('[size=2][font=serif]TEXT[/font][/size]')
        self.assertHTMLEqual(html, '<span style="font-size: 14.00%"><span style="font-family: serif">TEXT</span></span>')

    def test_font_and_font(self):
        html = render('[font=sans-serif][font=serif]TEXT[/font]')
        self.assertHTMLEqual(html, '<span style="font-family: sans-serif"><span style="font-family: serif">TEXT</span></span>')

    def test_two_font(self):
        html = render('[font=sans-serif,serif]TEXT[/font]')
        self.assertHTMLEqual(html, 'TEXT')

    def test_font_case(self):
        html = render('[font=Arial]TEXT[/font]')
        self.assertHTMLEqual(html, '<span style="font-family: arial">TEXT</span>')

        html = render('[font=arial]TEXT[/font]')
        self.assertHTMLEqual(html, '<span style="font-family: arial">TEXT</span>')

    def test_size(self):
        html = render('[size=2]TEXT[/size]')
        self.assertHTMLEqual(html, '<span style="font-size: 14.00%">TEXT</span>')

    def test_font(self):
        html = render('[font=serif]TEXT[/font]')
        self.assertHTMLEqual(html, '<span style="font-family: serif">TEXT</span>')

    def test_font_not_allowed(self):
        html = render('[font=Ubuntu]TEXT[/font]')
        self.assertHTMLEqual(html, """TEXT""")

    def test_code(self):
        html = render('`TEXT`')
        self.assertHTMLEqual(html, '<code class="notranslate">TEXT</code>')

    def test_code__with_backtick(self):
        html = render('``TE`XT``')
        self.assertHTMLEqual(html, '<code class="notranslate">TE`XT</code>')

    def test_note(self):
        html = render('a  ((NOTE)) ')
        self.assertHTMLEqual(html, 'a<small class="note">NOTE</small>')

    def test_footnote_with_default_transformer(self):
        html = render('a  ((NOTE)) ', transformers=DEFAULT_TRANSFORMERS)
        self.assertHTMLEqual(html, '''<p>
        a<a class="footnote" href="#fn-1" id="bfn-1">
        <span class="paren">
        [
        </span>1<span class="paren">
        ]
        </span>
        </a>
        </p><ul class="footnotes">
        <li>
        <a class="crosslink" href="#bfn-1" id="fn-1">
        1
        </a>: NOTE
        </li>
        </ul>
        ''')

    def test_mod_box(self):
        html = render('[mod=NAME]TEXT[/mod]')
        self.assertHTMLEqual(
            html,
            """<div class="moderated">
<p><strong>Moderated by<a class="crosslink user" href="http://ubuntuusers.local:8080/user/NAME/">NAME</a>:</strong>
</p>TEXT</div>""",
        )

    def test_mod_box_escaped(self):
        html = render('[mod=</a><span>BAR BAZ</span><a href="foo">]TEXT[/mod]')
        self.maxDiff = None

        self.assertHTMLEqual(
            html,
            """<div class="moderated">
<p>
<strong>
Moderated by<a class="crosslink user" href="http://ubuntuusers.local:8080/user/%3C/a%3E%3Cspan%3EBAR%20BAZ%3C/span%3E%3Ca%20href%3D%22foo%22%3E/">
&lt;/a&gt;&lt;span&gt;BAR BAZ&lt;/span&gt;&lt;a href=&quot;foo&quot;&gt;
</a>:
</strong>
</p>TEXT
</div>"""
        )


    def test_edit_box(self):
        html = render('[edit=NAME]TEXT[/edit]')
        self.assertHTMLEqual(
            html,
            """<div class="edited">
<p><strong>Edited by<a class="crosslink user" href="http://ubuntuusers.local:8080/user/NAME/">NAME</a>:</strong>
</p>TEXT</div>""",
        )

    def test_edit_box_escaped(self):
        html = render('''[edit=</a><script>console.log('hi')</script><a href="foo">]TEXT[/edit]''')
        self.assertHTMLEqual(
            html,
            '''<div class="edited">
<p>
<strong>
Edited by<a class="crosslink user" href="http://ubuntuusers.local:8080/user/%3C/a%3E%3Cscript%3Econsole.log%28%27hi%27%29%3C/script%3E%3Ca%20href%3D%22foo%22%3E/">
&lt;/a&gt;&lt;script&gt;console.log(&#x27;hi&#x27;)&lt;/script&gt;&lt;a href=&quot;foo&quot;&gt;
</a>:
</strong>
</p>TEXT
</div>'''
        )


    def test_mark(self):
        html = render('[mark]TEXT[/mark]')
        self.assertHTMLEqual(html, '<mark>TEXT</mark>')

    def test_mark_in_code(self):
        html = render('{{{ start [mark]TEXT[/mark] code}}}')
        self.assertHTMLEqual(
            html,
            """<pre class="notranslate">start<mark>TEXT</mark>code</pre>""",
        )

    def test_mark_control_characters(self):
        # excerpt from https://forum.ubuntuusers.de/post/6601232/
        html = render('''[mark] 6 @$0 1  91934 35 62 162

6

6 "4A6 ) 6 96366B,6,[/mark]''')
        self.assertHTMLEqual(
            html,
            "<mark> 6 @$0 1  91934 35 62 162 6 6 &quot;4A6 ) 6 96366B,6,</mark>",
        )

    def test_ruler(self):
        html = render('------')
        self.assertHTMLEqual(html, '<hr>')

    def test_div(self):
        html = render('{{|<style="margin:auto; max-width:1200px"> foo')
        self.assertHTMLEqual(
            html,
            """
            <div style="margin: auto; max-width: 1200px">
                <div class="contents">foo</div>
            </div>
            """,
        )

    def test_span(self):
        html = render("[[SPAN('text')]]")
        self.assertHTMLEqual(html, '<span>text</span>')

    def test_anchor(self):
        html = render('[[Anker(NAME)]]')
        self.assertHTMLEqual(
            html, '<a class="anchor crosslink" href="#NAME" id="NAME">⚓︎</a>'
        )

        html = render('[[Anchor(NAME)]]')
        self.assertHTMLEqual(
            html, '<a class="anchor crosslink" href="#NAME" id="NAME">⚓︎</a>'
        )

        html = render('[[Anchor(NA">"ME)]]')
        self.assertHTMLEqual(
            html, '<a class="anchor crosslink" href="#NA" id="NA">⚓︎</a>'
        )

        html = render('[[Anchor(NA">ME)]]')
        self.assertHTMLEqual(
            html,
            """<a class="crosslink anchor" href='#NA"&gt;ME' id='NA"&gt;ME'>⚓︎</a>"""
        )

    def test_newline(self):
        html = render("""a \\\\
b""")
        self.assertHTMLEqual(html, 'a<br>b')

    def test_break(self):
        html = render('[[BR]]')
        self.assertHTMLEqual(html, '<br>')

    def test_not_existing_macro(self):
        html = render('[[BROOOO]]')
        self.assertHTMLEqual(
            html,
            """<div class="error">
<strong>Missing macro</strong>
<p>The macro “BROOOO” does not exist.</p>
</div>
""",
        )

    def test_template_no_argument(self):
        html = render('[[Template()]]')
        self.assertHTMLEqual(
            html,
            """<div class="error">
<strong>Invalid arguments</strong>
<p>The first argument must be the name of the template.</p>
</div>""",
        )

    def test_user_interwiki_link(self):
        html = render('[user:foobar:]')
        self.assertHTMLEqual(
            html,
            '<a class="crosslink user" href="http://ubuntuusers.local:8080/user/foobar/">foobar</a>',
        )

    def test_ikhaya_interwiki_link(self):
        html = render('[ikhaya:1:]')
        self.assertHTMLEqual(
            html,
            '<a class="crosslink ikhaya" href="http://ubuntuusers.local:8080/ikhaya/1/">1</a>',
        )

        html = render('[ikhaya:foobar/baz:]')
        self.assertHTMLEqual(
            html,
            """
        <a class="crosslink ikhaya" href="http://ikhaya.ubuntuusers.local:8080/foobar/baz/">foobar/baz</a>""",
        )

    def test_source_link(self):
        html = render(""" just some text [1]

[1]: reference""")

        self.assertHTMLEqual(
            html,
            (
                """just some text<sup>
<a href="#source-1">
[1]
</a>
</sup><sup>
<a href="#source-1">
[1]
</a>
</sup>: reference
"""
            ),
        )

    def test_definition_list(self):
        html = render(
            """ a::
                    foo
                b::
                    bar
            """
        )
        self.assertHTMLEqual(
            html,
            (
                """<dl>
<dt>
a
</dt><dd>
foo
</dd><dt>
 b
</dt><dd>
bar
</dd>
</dl>"""
            ),
        )

    def test_code_highlight(self):
        html = render("""{{{#!code bash
#!/bin/bash
cp ~/.bash_profile ~/.bash_profile.back

# autologin for user instead of root
sed -i 's/root/arch/' $HOME/.bash_profile
}}}""")
        self.maxDiff = None
        self.assertHTMLEqual(
            html,
            """<div class="code"><div class="notranslate syntax">
        <table class="notranslate syntaxtable"><tr><td class="linenos"><div class="linenodiv"><pre>
        <span class="normal">
        1
        </span><span class="normal">
        2
        </span><span class="normal">
        3
        </span><span class="normal">
        4
        </span><span class="normal">
        5
        </span>
        </pre></div></td><td class="code"><div><pre><span></span><span class="ch">#!/bin/bash</span>
        cp<span class="w"> </span>~/.bash_profile<span class="w"> </span>~/.bash_profile.back

        <span class="c1"># autologin for user instead of root</span>
        sed<span class="w"> </span>-i<span class="w"> </span><span class="s1">&#39;s/root/arch/&#39;</span><span class="w"> </span><span class="nv">$HOME</span>/.bash_profile
        </pre></div>
        </td></tr></table></div></div>""",
        )

    def test_control_characters_stripped_in_code(self):
        html = render('{{{ \x00\x07 t }}}')
        self.maxDiff = None
        self.assertHTMLEqual(
            html,
            '<pre class="notranslate">t</pre>'
        )

        html = render('''{{{#!code bash
                       \x00\x07
                       foo
                      }}}''')
        self.assertHTMLEqual(
            html,
            '''<div class="code"><div class="notranslate syntax"><table class="notranslate syntaxtable"><tr><td class="linenos"><div class="linenodiv"><pre><span class="normal">1</span>
<span class="normal">2</span>
<span class="normal">3</span></pre></div></td><td class="code"><div><pre><span></span><span class="w">                       </span>
<span class="w">                       </span>foo
<span class="w">                      </span>
</pre></div></td></tr></table></div>
</div>''')

        # excerpt from https://forum.ubuntuusers.de/post/1828238/
        html = render('''{{{#!code html
(II) fglrx(0):  H361C171WU1
(II) fglrx(0):  2AIl¹ÿ
(II) fglrx(0): EDID (in hex):
        }}}''')
        self.assertHTMLEqual(html, '''<div class="code"><div class="notranslate syntax"><table class="notranslate syntaxtable"><tr><td class="linenos"><div class="linenodiv"><pre><span class="normal">1</span>
<span class="normal">2</span>
<span class="normal">3</span>
<span class="normal">4</span>
<span class="normal">5</span></pre></div></td><td class="code"><div><pre><span></span>(II) fglrx(0):  H361C171WU1
(II) fglrx(0):
2AIl¹ÿ
(II) fglrx(0): EDID (in hex):

</pre></div></td></tr></table></div>
</div>
        ''')

    def test_csv_to_table(self):
        html = render("""{{{#!csv
Device,Clicks,Impressions,CTR,Position
Desktop,12167283,120602930,10.09%,14.28
Mobile,899256,20140779,4.46%,19.78
Tablet,167759,1843644,9.1%,8.63
}}}""")
        self.assertHTMLEqual(
            html,
            """<table>
        <tr><td>Device</td><td>Clicks</td><td>Impressions</td><td>CTR</td><td>Position</td></tr>
        <tr><td>Desktop</td><td>12167283</td><td>120602930</td><td>10.09%</td><td>14.28</td></tr>
        <tr><td>Mobile</td><td>899256</td><td>20140779</td><td>4.46%</td><td>19.78</td></tr>
        <tr><td>Tablet</td><td>167759</td><td>1843644</td><td>9.1%</td><td>8.63</td></tr>
        </table>""",
        )

    def test_table_alignment(self):
        html = render("""||<(>a ||<:>b ||<)>c ||<^>d ||<v>e ||<: cellstyle="background-color:#ff0000;"> f ||""")
        self.assertHTMLEqual(html,"""<table>
            <tr>
            <td style="text-align: left">
            a
            </td><td style="text-align: center">
            b
            </td><td style="text-align: right">
            c
            </td><td style="vertical-align: top">
            d
            </td><td style="vertical-align: bottom">
            e
            </td><td style="text-align: center; background-color: #ff0000">
            f
            </td>
            </tr>
            </table>""")

    def test_box_alignment(self):
        html = render("{{|<^>foo \n |}}")
        self.assertHTMLEqual(html, '''<div style="text-align: top">
            <div class="contents">
            foo
            </div>
            </div>''')

    def test_long_link(self):
        html = render(
            'https://wiki.ubuntuusers.de/Ablage_%28Speicherung_im_Forum_-No_Paste_Service-%29/')
        self.assertHTMLEqual(html, '''
        <a class="external" href="https://wiki.ubuntuusers.de/Ablage_%28Speicherung_im_Forum_-No_Paste_Service-%29/"
           rel="nofollow"
           title="https://wiki.ubuntuusers.de/Ablage_%28Speicherung_im_Forum_-No_Paste_Service-%29/">
        https://wiki.ubuntuusers.de/Ablage_%28Speicherung_im_Forum_-No_Paste_Service-%29/
        </a>''')

    def test_interwiki_link(self):
        html = render("[attachment:a:]")
        self.assertHTMLEqual(html, '''
        <a class="interwiki interwiki-attachment" href="http://wiki.ubuntuusers.local:8080/_attachment/?target=a">
        a
        </a>''')

    def test_external_link(self):
        html = render(
            '[https://wiki.ubuntuusers.de/Ablage_%28Speicherung_im_Forum_-No_Paste_Service-%29/]')
        self.assertHTMLEqual(html, '''
        <a class="external" href="https://wiki.ubuntuusers.de/Ablage_%28Speicherung_im_Forum_-No_Paste_Service-%29/" rel="nofollow" title="https://wiki.ubuntuusers.de/Ablage_%28Speicherung_im_Forum_-No_Paste_Service-%29/">
        https://wiki.ubuntuusers.de/Ablage_%28Speicherung_im_Forum_-No_Paste_Service-%29/
        </a>''')

    def test_javascript_link(self):
        html = render("[javascript:alert('foo')]")
        self.assertHTMLEqual(html, '[javascript:alert(&#x27;foo&#x27;)]')

    def test_mailto_link(self):
        html = render('[mailto:foo@bar.test]')
        self.assertHTMLEqual(html, '''
        <a class="crosslink" href="mailto:foo@bar.test" title="mailto:foo@bar.test">
        foo@bar.test
        </a>''')

    def test_invalid_parser(self):
        html = render('{{{#!not_existing_parser_1233456767867899789\ncONTENT}}}')
        self.assertHTMLEqual(html, '<pre class="notranslate">cONTENT</pre>')

    def test_lists(self):
        """Check list rendering."""
        html = render(' * 1\n * 2\n  1. 3\n * 4')
        self.assertHTMLEqual(
            html,
            (
                '<ul>'
                '<li>1</li>'
                '<li>2<ol class="arabic">'
                '<li>3</li>'
                '</ol></li>'
                '<li>4</li>'
                '</ul>'
            ),
        )

    def test_blockquotes(self):
        """Test block quote rendering."""
        html = render("> ''foo\n> bar''\n>> nested")
        self.assertHTMLEqual(
            html,
            (
                '<blockquote>'
                '<em>foo\nbar</em>'
                '<blockquote>nested</blockquote>'
                '</blockquote>'
            ),
        )

    def test_topic_link_with_whitespace(self):
        """Test topic link rendering with whitespace in target and description."""
        html = render('[topic: with : whitespace ]')
        self.assertHTMLEqual(
            html,
            (
                '<a href="http://forum.ubuntuusers.local:8080/topic/with/" class="crosslink topic">'
                'whitespace'
                '</a>'
            ),
        )

    def test_wiki_link_with_whitespace(self):
        """Test wiki link rendering with whitespace in target."""
        html = render('[: page :]')
        self.assertHTMLEqual(
            html,
            (
                '<a href="http://wiki.ubuntuusers.local:8080/page/" class="internal missing">'
                'page'
                '</a>'
            ),
        )

    def test_wikilink_with_anchor_no_description(self):
        html = render('[:foo#anchor:]')

        link = '<a href="{url}" class="internal missing">foo (section \u201canchor\u201d)</a>'
        link = link.format(url=href('wiki', 'foo', _anchor='anchor'))
        self.assertHTMLEqual(html, link)

    @override_settings(LANGUAGE_CODE='de-DE')
    def test_localized_wikilink_with_anchor_no_description(self):
        html = render('[:foo#anchor:]')

        link = '<a href="{url}" class="internal missing">foo (Abschnitt \u201eanchor\u201c)</a>'
        link = link.format(url=href('wiki', 'foo', _anchor='anchor'))
        self.assertHTMLEqual(html, link)

    def test_heading(self):
        html = render('''= a =\n\n== B ==\n\ntext''')
        self.assertHTMLEqual(
            html, '''<h2 id="a">a<a href="#a" class="headerlink">¶</a></h2>
<h3 id="B">B<a href="#B" class="headerlink">¶</a></h3>
text'''
        )

    def test_heading_with_default_transformers(self):
        html = render('''= a =\n\n== B ==\n\ntext''', transformers=DEFAULT_TRANSFORMERS)
        self.assertHTMLEqual(
            html, '''<section class="section_1"><h2 id="a">a<a href="#a" class="headerlink">¶</a></h2>
            <section class="section_2"><h3 id="B">B<a href="#B" class="headerlink">¶</a></h3><p>
text</p></section></section>'''
        )

    def test_bold_link__to_escape(self):
        html = render("""'''<a href="foo"></a>'''""")
        self.assertEqual(html, '<strong>&lt;a href=&quot;foo&quot;&gt;&lt;/a&gt;</strong>')

    def test_heading_contains_arrow(self):
        html = render_smilies('= => g =')
        self.assertHTMLEqual(
            html, '<h2 id="g">\u21d2 g<a href="#g" class="headerlink">\xb6</a></h2>'
        )

    def test_arrows(self):
        html = render_smilies('a => this')
        self.assertHTMLEqual(html, 'a \u21d2 this')

    def test_list_with_arrow(self):
        html = render_smilies(' - -> this')
        self.assertHTMLEqual(html, '<ul><li>\u2192 this</li></ul>')

    def test_strikethrough_with_dash(self):
        html = render_smilies('a -- --(dvdfv)--')
        self.assertHTMLEqual(html, 'a \u2013 <del>dvdfv</del>')

    def test_arrow_in_bracket(self):
        html = render_smilies('(-> d)')
        self.assertHTMLEqual(html, '(\u2192 d)')

    def test_compile(self):
        """
        Test alternative way to render with compile.
        See __init__.py for more information.
        """
        from inyoka.markup.base import parse, render

        node = parse("Hello World!\n\n''foo bar spam''")
        code = node.compile('html')
        html = render(code, RenderContext())
        self.assertHTMLEqual(html, '<p>Hello World!</p><p><em>foo bar spam</em></p>')

    def test_bigger_excerpt_with_default_transformers(self):
        self.maxDiff = None
        html = render('''Word

||a||b||

{{{ a }}}

= head =

para

 * 1
 * 2

= head =

 * 3
 * 4

 * 5
 * 6

= head =
== subhead ==

word ''', transformers=DEFAULT_TRANSFORMERS)
        self.assertHTMLEqual(
            html, '''
<p>Word</p>
<table><tr><td>a</td><td>b</td></tr></table>
<pre class="notranslate"> a </pre>
<section class="section_1"><h2 id="head">head<a href="#head" class="headerlink">¶</a></h2>
<p>para</p>
<ul><li><p>1</p></li><li><p>2</p></li></ul>
</section><section class="section_1"><h2 id="head-2">head<a href="#head-2" class="headerlink">¶</a></h2>
<ul><li><p>3</p></li><li><p>4</p></li></ul>
<ul><li><p>5</p></li><li><p>6</p></li></ul></section>
<section class="section_1"><h2 id="head-3">head<a href="#head-3" class="headerlink">¶</a></h2>
<section class="section_2"><h3 id="subhead">subhead<a href="#subhead" class="headerlink">¶</a></h3>
<p>word </p></section></section>'''
        )


class TestTemplateHtmlRenderer(TestCase):
    def setUp(self):
        user = User.objects.create_user('test_user', 'test@inyoka.local')

        note_markup = """{{|<title="Note:" class="box notice">
        <@ $arguments @>
        |}}
        """
        Page.objects.create(
            name=path.join(settings.WIKI_TEMPLATE_BASE, 'Note'),
            text=note_markup,
            user=user,
        )

        command_markup = '{{|<class="bash">{{{<@ $arguments @> }}}|}}'
        Page.objects.create(
            name=path.join(settings.WIKI_TEMPLATE_BASE, 'Command'),
            text=command_markup,
            user=user,
        )

        table_markup = """||<@ for $line in $arguments split_by '
' @>
<@ if $line as stripped contains '+++' @>
||<@ else @>
<@ $line @> ||
<@ endif @>
<@ endfor @>"""
        Page.objects.create(
            name=path.join(settings.WIKI_TEMPLATE_BASE, 'Table'),
            text=table_markup,
            user=user,
        )

    def test_list_inside_a_template(self):
        markup = """[[Vorlage(Note, "Text inside a template not in a list.

 * some text in a list.
 * another element")]]
        """
        html = render(markup)
        self.assertHTMLEqual(
            html,
            """<div class="box notice"><h3 class="box notice">Note:</h3><div class="contents"><p>
        Text inside a template not in a list.</p><ul><li><p>some text in a list.</p></li><li><p>another element</p></li></ul><p>        </p></div></div><p>
        </p>""",
        )

    def test_template_inside_template(self):
        markup = r"""{{{#!vorlage Note
Type the following
{{{#!vorlage Command
start
\}}}
to start it.
}}}
"""
        html = render(markup)
        self.assertHTMLEqual(
            html,
            """<div class="box notice"><h3 class="box notice">Note:</h3><div class="contents"><p>
        Type the following
</p><div class="bash"><div class="contents"><pre class="notranslate">start </pre></div></div><p>
to start it.
        </p></div></div><p>
        </p>""",
        )

    def test_template_inside_template_same_line(self):
        markup = """{{{#!vorlage Note
Type the following [[Vorlage(Command, start)]] to start it.
}}}
"""
        html = render(markup)
        self.assertHTMLEqual(
            html,
            """<div class="box notice"><h3 class="box notice">Note:</h3><div class="contents"><p>
        Type the following </p><div class="bash"><div class="contents"><pre class="notranslate">start </pre></div></div><p> to start it.
        </p></div></div><p>
        </p>""",
        )

    def test_template_inside_table_template(self):
        markup = """{{{#!vorlage Table
<rowclass="head"> Command
Description
+++
[[Vorlage (Command, "start")]]
Text
}}}
"""
        html = render(markup)
        self.assertHTMLEqual(
            html,
            """<table><tr class="head"><td> Command </td><td> Description </td></tr><tr><td> <div class="bash"><div class="contents"><pre class="notranslate">start </pre></div></div> </td><td> Text </td></tr></table>""",
        )
