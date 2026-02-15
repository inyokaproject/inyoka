"""
tests.utils.test_utils
~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2007-2026 by the Inyoka Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

import feedparser
import nh3

from inyoka.planet.models import Blog
from inyoka.planet.tasks import planet_cleaner
from inyoka.portal.user import User
from inyoka.utils.html import cleanup_html
from inyoka.utils.test import TestCase


class TestHTML(TestCase):
    def test_cleanup_html_paragraphs(self):
        self.assertEqual(cleanup_html('Foo Bar', planet_cleaner()), '<p>Foo Bar</p>')
        self.assertEqual(cleanup_html('<p>Foo Bar', planet_cleaner()), '<p>Foo Bar</p>')
        self.assertEqual(
            cleanup_html('Foo Bar</p>', planet_cleaner()), '<p>Foo Bar</p><p></p>'
        )
        self.assertEqual(
            cleanup_html('<p>Foo Bar</p>', planet_cleaner()), '<p>Foo Bar</p>'
        )

    def test_cleanup_html_a(self):
        self.assertEqual(
            cleanup_html('<a href=foo_bar.png></a>', planet_cleaner()),
            '<a href="foo_bar.png" rel="noopener noreferrer"></a>',
        )
        self.assertEqual(
            cleanup_html('<a href="foo_bar.png"></a>', planet_cleaner()),
            '<a href="foo_bar.png" rel="noopener noreferrer"></a>',
        )
        self.assertEqual(
            cleanup_html("<a href='foo_bar.png'></a>", planet_cleaner()),
            '<a href="foo_bar.png" rel="noopener noreferrer"></a>',
        )

    def test_cleanup_html_img(self):
        self.user = User.objects.register_user(
            'testing', 'example@example.com', 'pwd', False
        )
        Blog.objects.create(
            name='Testblog',
            blog_url='http://example.test/',
            feed_url='http://example.test/feed',
            user=self.user,
            active=True,
        )

        self.assertEqual(
            cleanup_html(
                '<img src="https://example.test/foo_bar.png">', planet_cleaner()
            ),
            '<img src="https://example.test/foo_bar.png">',
        )

        self.assertEqual(
            cleanup_html(
                '<img src="https://example.org/foo_bar.png">', planet_cleaner()
            ),
            '<img>',
        )

    def test_cleanup_html_entity(self):
        self.assertEqual(
            cleanup_html('foo a &amp; b &#60; c &#X3C; test', planet_cleaner()),
            '<p>foo a & b < c < test</p>',
        )

    def test_add_paragraphs_fragments(self):
        fragment = '<h1>Parse me!</h1>Foo'

        self.assertHTMLEqual(
            cleanup_html(fragment, planet_cleaner()), '<h1>Parse me!</h1><p>Foo</p>'
        )

    def test_rss_feed(self):
        feed_string = """
<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel>
<title>C3VO</title>
<link>https://c3vo.de/</link>
<description></description>
<atom:link href="https://c3vo.de/feeds/rss" rel="self"></atom:link>
<lastBuildDate>Wed, 05 Aug 2020 19:00:00 +0200</lastBuildDate>
<item>
<title>Mirror von gitlab zu github</title>
<link>https://c3vo.de/home/mirror-gitlab-github/</link>
<description>&lt;p&gt;Die &lt;a href="https://gitlab.com/help/user/project/repository/repository_mirroring.md"&gt;gitlab Dokumentation&lt;/a&gt;
empfiehlt zum Spiegeln meiner Meinung nach zu stark das Nutzen von github
&lt;a href="https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token"&gt;personal access tokens&lt;/a&gt;.&lt;/p&gt;
&lt;p&gt;Diese haben aber einen Nachteil: Personal access tokens gelten für alle
Repositories eines Nutzer. Anders formuliert: Gibt man einem personal
access token Schreibrechte, kann man mit diesem token in alle
Repositories dieses Nutzers schreiben. Gewollt ist in meinem Fall jedoch eher,
dass man Schreibrechte für &lt;em&gt;das eine&lt;/em&gt; Repository zum Spiegeln vergibt.&lt;/p&gt;
&lt;p&gt;github hat &lt;a href="https://docs.github.com/en/developers/overview/managing-deploy-keys#deploy-keys"&gt;deploy keys&lt;/a&gt;
, die nur lesen/schreiben &lt;em&gt;pro Repository&lt;/em&gt; ermöglichen.
Diese kann man auch für das Spiegeln von gitlab zu github nutzen.&lt;/p&gt;
&lt;p&gt;Da das aber in den beiden Dokumentationen subjektiv eher implizit steht, hier einmal die konkreten Schritte:&lt;/p&gt;
&lt;ol&gt;
&lt;li&gt;Ziel-Repository auf github erstellen&lt;/li&gt;
&lt;li&gt;mirror in gitlab einrichten&lt;ol&gt;
&lt;li&gt;im bestehenden gitlab-Repository „Repository Settings“ → „Mirroring repositories“ öffnen&lt;/li&gt;
&lt;li&gt;Github-Repository-URL eingeben. Fallstrick hier: &lt;code&gt;ssh://&lt;/code&gt; vorn an SSH-Repo-Adresse aus github, später den &lt;code&gt;:&lt;/code&gt; durch &lt;code&gt;/&lt;/code&gt; ersetzen. Also aus &lt;code&gt;git@github.com:&amp;lt;user&amp;gt;/&amp;lt;repo&amp;gt;.git&lt;/code&gt; wird &lt;code&gt;ssh://git@github.com/&amp;lt;user&amp;gt;/&amp;lt;repo&amp;gt;.git&lt;/code&gt;. Andernfalls mag gitlab die URL nicht.&lt;/li&gt;
&lt;li&gt;Erscheinenden „Detect host keys.“-Button klicken und den Fingerprint mit dem von &lt;a href="https://docs.github.com/en/github/authenticating-to-github/githubs-ssh-key-fingerprints"&gt;github&lt;/a&gt; vergleichen.&lt;/li&gt;
&lt;li&gt;Mirror direction „push“ auswählen.&lt;/li&gt;
&lt;li&gt;Bei „Authentication method“ „SSH public key“ wählen → damit wird ein eigener SSH-Key im gitlab erstellt.&lt;/li&gt;
&lt;li&gt;Den generierten SSH public key aus gitlab kopieren und in github als deploy key einfügen. Dieser braucht in github Schreibrechte.&lt;/li&gt;
&lt;li&gt;im gitlab „update now“ drücken und schauen, ob es funktioniert.&lt;/li&gt;
&lt;/ol&gt;
&lt;/li&gt;
&lt;/ol&gt;
&lt;p&gt;Dann sollte es gehen. 🙂&lt;/p&gt;</description>
<dc:creator xmlns:dc="http://purl.org/dc/elements/1.1/">Christoph</dc:creator>
<pubDate>Wed, 05 Aug 2020 19:00:00 +0200</pubDate>
<guid>tag:c3vo.de,2020-08-05:home/mirror-gitlab-github/</guid>
<category>uu-planet</category>
<category>Open Source</category>
<category>gitlab</category>
<category>github</category>
</item>
</channel></rss>
        """

        feed = feedparser.parse(feed_string)
        entry = feed.entries[0]

        title = entry.title_detail.get('value') or ''
        title = nh3.clean(title, tags=set())
        self.assertEqual(title, 'Mirror von gitlab zu github')

        html_string = """
<p>Die <a href="https://gitlab.com/help/user/project/repository/repository_mirroring.md" rel="noopener noreferrer">gitlab Dokumentation</a> empfiehlt zum Spiegeln meiner Meinung nach zu stark das Nutzen von github <a href="https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token"  rel="noopener noreferrer">personal access tokens</a>.</p>
<p>Diese haben aber einen Nachteil: Personal access tokens gelten für alle Repositories eines Nutzer. Anders formuliert: Gibt man einem personal access token Schreibrechte, kann man mit diesem token in alle Repositories dieses Nutzers schreiben. Gewollt ist in meinem Fall jedoch eher, dass man Schreibrechte für <em>das eine</em> Repository zum Spiegeln vergibt.</p>
<p>github hat <a href="https://docs.github.com/en/developers/overview/managing-deploy-keys#deploy-keys"  rel="noopener noreferrer">deploy keys</a> , die nur lesen/schreiben <em>pro Repository</em> ermöglichen. Diese kann man auch für das Spiegeln von gitlab zu github nutzen.</p>
<p>Da das aber in den beiden Dokumentationen subjektiv eher implizit steht, hier einmal die konkreten Schritte:</p>
<ol>
<li>Ziel-Repository auf github erstellen</li>
<li>mirror in gitlab einrichten<ol>
<li>im bestehenden gitlab-Repository „Repository Settings“ → „Mirroring repositories“ öffnen</li>
<li>Github-Repository-URL eingeben. Fallstrick hier: <code>ssh://</code> vorn an SSH-Repo-Adresse aus github, später den <code>:</code> durch <code>/</code> ersetzen. Also aus <code>git@github.com:<user>/<repo>.git</code> wird <code>ssh://git@github.com/<user>/<repo>.git</code>. Andernfalls mag gitlab die URL nicht.</li><li>Erscheinenden „Detect host keys.“-Button klicken und den Fingerprint mit dem von <a href="https://docs.github.com/en/github/authenticating-to-github/githubs-ssh-key-fingerprints" rel="noopener noreferrer">github</a> vergleichen.</li><li>Mirror direction „push“ auswählen.</li><li>Bei „Authentication method“ „SSH public key“ wählen → damit wird ein eigener SSH-Key im gitlab erstellt.</li><li>Den generierten SSH public key aus gitlab kopieren und in github als deploy key einfügen. Dieser braucht in github Schreibrechte.</li><li>im gitlab „update now“ drücken und schauen, ob es funktioniert.</li></ol></li></ol><p>Dann sollte es gehen. 🙂</p>
"""

        text = entry.get('summary_detail').get('value')
        text = cleanup_html(text, planet_cleaner())

        self.assertHTMLEqual(text, html_string)

    def test_rss_feed__plain_text(self):
        feed_string = """
<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel>
<title>C3VO</title>
<link>https://c3vo.de/</link>
<description></description>
<atom:link href="https://c3vo.de/feeds/rss" rel="self"></atom:link>
<lastBuildDate>Wed, 05 Aug 2020 19:00:00 +0200</lastBuildDate>
<item>
<title>Mirror von gitlab zu github</title>
<link>https://c3vo.de/home/mirror-gitlab-github/</link>
<description>Just a small test with plain text</description>
<dc:creator xmlns:dc="http://purl.org/dc/elements/1.1/">Christoph</dc:creator>
<pubDate>Wed, 05 Aug 2020 19:00:00 +0200</pubDate>
<guid>tag:c3vo.de,2020-08-05:home/mirror-gitlab-github/</guid>
</item>
</channel></rss>
        """

        feed = feedparser.parse(feed_string)
        entry = feed.entries[0]

        text = entry.get('summary_detail').get('value')
        text = cleanup_html(text, planet_cleaner())

        self.assertHTMLEqual(text, '<p>Just a small test with plain text</p>')

    def test_header_id(self):
        html = """<h2 class="wp-h" id="header-4242">Test</h2>"""
        self.assertEqual(cleanup_html(html, planet_cleaner()), '<h2>Test</h2>')
