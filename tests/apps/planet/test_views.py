from datetime import datetime
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
                             pub_date=datetime.now(), updated=datetime.now())
        Entry.objects.create(blog=blog, url="http://example.com/article2",
                             guid="http://example.com/article2",
                             text="This is a test", title="I have a title",
                             pub_date=datetime.now(), updated=datetime.now())

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

        now = datetime.now().replace(microsecond=0)
        Entry.objects.create(blog=blog, url="http://example.com/article1",
                             guid="http://example.com/article1",
                             text="This is a test", title="Test title",
                             pub_date=now, updated=now,
                             author='AnonymousAuthor', author_homepage='https://example.com')

        response = self.client.get('/feeds/full/10/')

        feed = feedparser.parse(response.content)

        # feed properties
        self.assertEqual(feed.feed.title, 'ubuntuusers.local:8080 planet')
        self.assertEqual(feed.feed.title_detail.type, 'text/plain')
        self.assertEqual(feed.feed.title_detail.language, None)
        self.assertEqual(feed.feed.id, 'http://planet.ubuntuusers.local:8080/')
        self.assertEqual(feed.feed.link, 'http://planet.ubuntuusers.local:8080/')

        feed_updated = datetime.fromtimestamp(mktime(feed.feed.updated_parsed))
        self.assertEqual(feed_updated, now)

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
        self.assertEqual(len(entry.content), 1)
        self.assertEqual(entry.content[0].value, 'This is a test')
        self.assertEqual(entry.content[0].type, 'application/xhtml+xml')
        self.assertFalse('summary_detail' in entry)
        self.assertFalse('text' in entry)
        self.assertFalse('created_parsed' in entry)

        entry_published = datetime.fromtimestamp(mktime(entry.published_parsed))
        self.assertEqual(entry_published, now)

        entry_date = datetime.fromtimestamp(mktime(entry.date_parsed))
        self.assertEqual(entry_date, now)

        entry_updated = datetime.fromtimestamp(mktime(entry.updated_parsed))
        self.assertEqual(entry_updated, now)

        self.assertEqual(entry.author, 'AnonymousAuthor')
        self.assertEqual(entry.author_detail.name, 'AnonymousAuthor')
        self.assertEqual(entry.author_detail.href, 'https://example.com')
