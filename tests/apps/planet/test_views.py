"""
    tests.apps.planet.test_views
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test planet views.

    :copyright: (c) 2012-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""


import datetime
from time import mktime

import feedparser
from django.conf import settings
from django.utils import translation

from inyoka.planet.models import Blog, Entry
from inyoka.portal.user import User
from inyoka.utils.test import InyokaClient, TestCase
from inyoka.utils.urls import href


class TestViews(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()
        self.admin = User.objects.register_user('admin', 'admin', 'admin', False)
        self.admin.is_superuser = True
        self.admin.save()

        self.client.defaults['HTTP_HOST'] = 'planet.%s' % settings.BASE_DOMAIN_NAME
        self.client.login(username='admin', password='admin')

    def test_empty_post_title(self):
        blog = Blog(name="Testblog", blog_url="http://example.com/",
                    feed_url="http://example.com/feed", user=self.admin,
                    active=True)
        blog.save()
        Entry.objects.create(blog=blog, url="http://example.com/article1",
                             guid="http://example.com/article1",
                             text="This is a test", title="",
                             pub_date=datetime.datetime.now(),
                             updated=datetime.datetime.now())
        Entry.objects.create(blog=blog, url="http://example.com/article2",
                             guid="http://example.com/article2",
                             text="This is a test", title="I have a title",
                             pub_date=datetime.datetime.now(),
                             updated=datetime.datetime.now())

        with translation.override('en-us'):
            response = self.client.post('/feeds/title/10/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No title given", count=1)

        with translation.override('en-us'):
            response = self.client.post('/feeds/short/10/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No title given", count=1)

        with translation.override('en-us'):
            response = self.client.post('/feeds/full/10/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No title given", count=1)

    def test_content_displayed(self):
        blog = Blog(name="Testblog", blog_url="http://example.com/",
                    feed_url="http://example.com/feed", user=self.admin,
                    active=True)
        blog.save()

        now = datetime.datetime.now().replace(microsecond=0)
        Entry.objects.create(blog=blog, url="http://example.com/article1",
                             guid="http://example.com/article1",
                             text="This is a test", title="Test title",
                             pub_date=now, updated=now,
                             author='AnonymousAuthor', author_homepage='https://example.com')

        with self.assertNumQueries(3):
            response = self.client.get('/feeds/full/10/')

        feed = feedparser.parse(response.content)

        # feed properties
        self.assertEqual(feed.feed.title, 'ubuntuusers.local:8080 planet')
        self.assertEqual(feed.feed.title_detail.type, 'text/plain')
        self.assertEqual(feed.feed.title_detail.language, 'en-us')
        self.assertEqual(feed.feed.id, 'http://planet.ubuntuusers.local:8080/')
        self.assertEqual(feed.feed.link, 'http://planet.ubuntuusers.local:8080/')

        feed_updated = datetime.datetime.fromtimestamp(mktime(feed.feed.updated_parsed))
        self.assertEqual(feed_updated, now - datetime.timedelta(hours=1))

        self.assertEqual(feed.feed.rights, href('portal', 'lizenz'))
        self.assertFalse('author' in feed.feed)
        self.assertFalse('author_detail' in feed.feed)

        # entry properties
        self.assertEqual(len(feed.entries), 1)
        entry = feed.entries[0]
        self.assertEqual(entry.id, 'http://example.com/article1')
        self.assertEqual(entry.link, 'http://example.com/article1')

        self.assertEqual(entry.title_detail.value, 'Test title')
        self.assertEqual(entry.title_detail.type, 'text/plain')
        self.assertEqual(entry.summary, 'This is a test')
        self.assertEqual(entry.summary_detail.type, 'text/html')
        self.assertFalse('text' in entry)
        self.assertFalse('created_parsed' in entry)

        entry_published = datetime.datetime.fromtimestamp(mktime(entry.published_parsed))
        self.assertEqual(entry_published, now - datetime.timedelta(hours=1))

        entry_date = datetime.datetime.fromtimestamp(mktime(entry.date_parsed))
        self.assertEqual(entry_date, now - datetime.timedelta(hours=1))

        entry_updated = datetime.datetime.fromtimestamp(mktime(entry.updated_parsed))
        self.assertEqual(entry_updated, now - datetime.timedelta(hours=1))

        self.assertEqual(entry.author, 'AnonymousAuthor')
        self.assertEqual(entry.author_detail.name, 'AnonymousAuthor')
        self.assertEqual(entry.author_detail.href, 'https://example.com')

    def test_export__foaf(self):
        Blog.objects.create(name="Testblog", blog_url="http://example.com/",
                    feed_url="http://example.com/feed", user=self.admin,
                    active=True)
        Blog.objects.create(name="Testblog2", blog_url="https://example.test/",
                            feed_url="https://example.test/feed", user=self.admin,
                            active=True)

        response = self.client.get('/blogs/export/foaf/')
        self.assertXMLEqual(response.content.decode(), f'''<?xml version="1.0"?>
<rdf:RDF
  xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
  xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"
  xmlns:foaf="http://xmlns.com/foaf/0.1/"
  xmlns:rss="http://purl.org/rss/1.0/"
  xmlns:dc="http://purl.org/dc/elements/1.1/"
>
<foaf:Group>

  <foaf:name>{ settings.BASE_DOMAIN_NAME } | Planet</foaf:name>
  <foaf:homepage>http://planet.{ settings.BASE_DOMAIN_NAME }/</foaf:homepage>
  <rdfs:seeAlso rdf:resource="http://planet.{ settings.BASE_DOMAIN_NAME }/blogs/export/foaf/" />


  <foaf:member>
    <foaf:Person>
      <foaf:name>Testblog</foaf:name>
      <foaf:weblog>
        <foaf:Document rdf:about="http://example.com/">
          <rdfs:seeAlso>
            <rss:channel rdf:about="http://example.com/feed" />
          </rdfs:seeAlso>
        </foaf:Document>
      </foaf:weblog>
    </foaf:Person>
  </foaf:member>

  <foaf:member>
    <foaf:Person>
      <foaf:name>Testblog2</foaf:name>
      <foaf:weblog>
        <foaf:Document rdf:about="https://example.test/">
          <rdfs:seeAlso>
            <rss:channel rdf:about="https://example.test/feed" />
          </rdfs:seeAlso>
        </foaf:Document>
      </foaf:weblog>
    </foaf:Person>
  </foaf:member>


</foaf:Group>
</rdf:RDF>''')

    def test_export__opml(self):
        Blog.objects.create(name="Testblog", blog_url="http://example.com/",
                    feed_url="http://example.com/feed", user=self.admin,
                    active=True)
        Blog.objects.create(name="Testblog2", blog_url="https://example.test/",
                            feed_url="https://example.test/feed", user=self.admin,
                            active=True)

        response = self.client.get('/blogs/export/opml/')
        self.assertXMLEqual(response.content.decode(), f'''<?xml version="1.0" encoding="utf8"?>
<opml version="1.1">
  <head>
    <title>{ settings.BASE_DOMAIN_NAME } | Planet</title>
  </head>
  <body>

      <outline type="rss" text="Testblog" htmlUrl="http://example.com/" xmlUrl="http://example.com/feed"/>

      <outline type="rss" text="Testblog2" htmlUrl="https://example.test/" xmlUrl="https://example.test/feed"/>

  </body>
</opml>''')

    def test_export__invalid_format(self):
        Blog.objects.create(name="Testblog", blog_url="http://example.com/",
                    feed_url="http://example.com/feed", user=self.admin,
                    active=True)

        response = self.client.get('/blogs/export/grml/')
        self.assertEqual(response.status_code, 404)
