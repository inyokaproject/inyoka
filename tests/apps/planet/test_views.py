"""
tests.apps.planet.test_views
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test planet views.

:copyright: (c) 2012-2026 by the Inyoka Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

import datetime

import feedparser
from django.conf import settings
from django.contrib.auth.models import Group
from django.core import mail
from django.core.cache import cache
from django.utils import timezone as dj_timezone
from django.utils import translation
from freezegun import freeze_time
from guardian.shortcuts import assign_perm

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
        blog = Blog(
            name='Testblog',
            blog_url='http://example.com/',
            feed_url='http://example.com/feed',
            user=self.admin,
            active=True,
        )
        blog.save()
        Entry.objects.create(
            blog=blog,
            url='http://example.com/article1',
            guid='http://example.com/article1',
            text='This is a test',
            title='',
            pub_date=dj_timezone.now(),
            updated=dj_timezone.now(),
        )
        Entry.objects.create(
            blog=blog,
            url='http://example.com/article2',
            guid='http://example.com/article2',
            text='This is a test',
            title='I have a title',
            pub_date=dj_timezone.now(),
            updated=dj_timezone.now(),
        )

        with translation.override('en-us'):
            response = self.client.post('/feeds/title/10/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No title given', count=1)

        with translation.override('en-us'):
            response = self.client.post('/feeds/short/10/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No title given', count=1)

        with translation.override('en-us'):
            response = self.client.post('/feeds/full/10/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No title given', count=1)

    def test_content_displayed(self):
        blog = Blog(
            name='Testblog',
            blog_url='http://example.com/',
            feed_url='http://example.com/feed',
            user=self.admin,
            active=True,
        )
        blog.save()

        now = dj_timezone.now().replace(microsecond=0)
        Entry.objects.create(
            blog=blog,
            url='http://example.com/article1',
            guid='http://example.com/article1',
            text='This is a test',
            title='Test title',
            pub_date=now,
            updated=now,
            author='AnonymousAuthor',
            author_homepage='https://example.com',
        )

        with self.assertNumQueries(3):
            response = self.client.get('/feeds/full/10/')

        feed = feedparser.parse(response.content)

        # feed properties
        self.assertEqual(feed.feed.title, 'ubuntuusers.local:8080 planet')
        self.assertEqual(feed.feed.title_detail.type, 'text/plain')
        self.assertEqual(feed.feed.title_detail.language, 'en-us')
        self.assertEqual(feed.feed.id, 'http://planet.ubuntuusers.local:8080/')
        self.assertEqual(feed.feed.link, 'http://planet.ubuntuusers.local:8080/')

        feed_updated = datetime.datetime.fromisoformat(feed.feed.updated)
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
        self.assertEqual(entry.summary, 'This is a test')
        self.assertEqual(entry.summary_detail.type, 'text/html')
        self.assertFalse('text' in entry)
        self.assertFalse('created_parsed' in entry)

        entry_published = datetime.datetime.fromisoformat(entry.published)
        self.assertEqual(entry_published, now)

        entry_date = datetime.datetime.fromisoformat(entry.date)
        self.assertEqual(entry_date, now)

        entry_updated = datetime.datetime.fromisoformat(entry.updated)
        self.assertEqual(entry_updated, now)

        self.assertEqual(entry.author, 'AnonymousAuthor')
        self.assertEqual(entry.author_detail.name, 'AnonymousAuthor')
        self.assertEqual(entry.author_detail.href, 'https://example.com')

    def test_export__foaf(self):
        Blog.objects.create(
            name='Testblog',
            blog_url='http://example.com/',
            feed_url='http://example.com/feed',
            user=self.admin,
            active=True,
        )
        Blog.objects.create(
            name='Testblog2',
            blog_url='https://example.test/',
            feed_url='https://example.test/feed',
            user=self.admin,
            active=True,
        )

        response = self.client.get('/blogs/export/foaf/')
        self.assertXMLEqual(
            response.content.decode(),
            f"""<?xml version="1.0"?>
<rdf:RDF
  xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
  xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"
  xmlns:foaf="http://xmlns.com/foaf/0.1/"
  xmlns:rss="http://purl.org/rss/1.0/"
  xmlns:dc="http://purl.org/dc/elements/1.1/"
>
<foaf:Group>

  <foaf:name>{settings.BASE_DOMAIN_NAME} | Planet</foaf:name>
  <foaf:homepage>http://planet.{settings.BASE_DOMAIN_NAME}/</foaf:homepage>
  <rdfs:seeAlso rdf:resource="http://planet.{settings.BASE_DOMAIN_NAME}/blogs/export/foaf/" />


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
</rdf:RDF>""",
        )

    def test_export__opml(self):
        Blog.objects.create(
            name='Testblog',
            blog_url='http://example.com/',
            feed_url='http://example.com/feed',
            user=self.admin,
            active=True,
        )
        Blog.objects.create(
            name='Testblog2',
            blog_url='https://example.test/',
            feed_url='https://example.test/feed',
            user=self.admin,
            active=True,
        )

        response = self.client.get('/blogs/export/opml/')
        self.assertXMLEqual(
            response.content.decode(),
            f"""<?xml version="1.0" encoding="utf8"?>
<opml version="1.1">
  <head>
    <title>{settings.BASE_DOMAIN_NAME} | Planet</title>
  </head>
  <body>

      <outline type="rss" text="Testblog" htmlUrl="http://example.com/" xmlUrl="http://example.com/feed"/>

      <outline type="rss" text="Testblog2" htmlUrl="https://example.test/" xmlUrl="https://example.test/feed"/>

  </body>
</opml>""",
        )

    def test_export__invalid_format(self):
        Blog.objects.create(
            name='Testblog',
            blog_url='http://example.com/',
            feed_url='http://example.com/feed',
            user=self.admin,
            active=True,
        )

        response = self.client.get('/blogs/export/grml/')
        self.assertEqual(response.status_code, 404)

    def test_hide_entry_get(self):
        blog = Blog(
            name='Testblog',
            blog_url='http://example.com/',
            feed_url='http://example.com/feed',
            user=self.admin,
            active=True,
        )
        blog.save()

        entry = Entry.objects.create(
            blog=blog,
            url='http://example.com/article1',
            guid='http://example.com/article1',
            text='This is a test',
            title='',
            pub_date=dj_timezone.now(),
            updated=dj_timezone.now(),
        )

        response = self.client.get(f'/hide/{entry.id}/', follow=True)
        self.assertContains(response, 'Are you sure you want to hide the entry?')
        self.assertRedirects(response, href('planet'))

    def test_hide_entry_post(self):
        blog = Blog(
            name='Testblog',
            blog_url='http://example.com/',
            feed_url='http://example.com/feed',
            user=self.admin,
            active=True,
        )
        blog.save()

        entry = Entry.objects.create(
            blog=blog,
            url='http://example.com/article1',
            guid='http://example.com/article1',
            text='This is a test',
            title='',
            pub_date=dj_timezone.now(),
            updated=dj_timezone.now(),
        )

        response = self.client.post(f'/hide/{entry.id}/', follow=True)
        self.assertContains(response, 'was successfully hidden')
        self.assertRedirects(response, href('planet'))

        entry.refresh_from_db()
        self.assertTrue(entry.hidden)

    def test_restore_entry(self):
        blog = Blog(
            name='Testblog',
            blog_url='http://example.com/',
            feed_url='http://example.com/feed',
            user=self.admin,
            active=True,
        )
        blog.save()

        entry = Entry.objects.create(
            blog=blog,
            url='http://example.com/article1',
            guid='http://example.com/article1',
            text='This is a test',
            title='',
            pub_date=dj_timezone.now(),
            updated=dj_timezone.now(),
            hidden=True,
        )

        response = self.client.post(f'/hide/{entry.id}/', follow=True)
        self.assertContains(response, 'was successfully restored')
        self.assertRedirects(response, href('planet'))

        entry.refresh_from_db()
        self.assertFalse(entry.hidden)

    def test_hide_entry_post__cancel(self):
        blog = Blog(
            name='Testblog',
            blog_url='http://example.com/',
            feed_url='http://example.com/feed',
            user=self.admin,
            active=True,
        )
        blog.save()

        entry = Entry.objects.create(
            blog=blog,
            url='http://example.com/article1',
            guid='http://example.com/article1',
            text='This is a test',
            title='',
            pub_date=dj_timezone.now(),
            updated=dj_timezone.now(),
        )

        response = self.client.post(
            f'/hide/{entry.id}/', data={'cancel': True}, follow=True
        )
        self.assertContains(response, 'Canceled')
        self.assertRedirects(response, href('planet'))


class IndexMixin:
    client_class = InyokaClient

    def setUp(self):
        super().setUp()

        self.user = User.objects.register_user('user', 'user', 'user', False)
        self.user.save()

        self.client.defaults['HTTP_HOST'] = 'planet.%s' % settings.BASE_DOMAIN_NAME

    def _assign_user_privileges(self):
        registered_group = Group.objects.get(name=settings.INYOKA_REGISTERED_GROUP_NAME)
        assign_perm('planet.hide_entry', registered_group)

    def _create_blog_with_entry(self, adjustments_blog: dict={}, adjustments_entry: dict={}):
        blog_args = {
            'name': 'Testblog',
            'blog_url': 'http://example.com/',
            'feed_url': 'http://example.com/feed',
            'user': self.user,
            'active': True,
        }
        blog_args.update((key, adjustments_blog[key]) for key in adjustments_blog.keys())

        blog = Blog(**blog_args)
        blog.save()

        entry_args = {
            'blog': blog,
            'url': 'http://example.com/article1',
            'guid': 'http://example.com/article1',
            'text': 'This is a test',
            'title': 'testTitle',
            'pub_date': dj_timezone.now(),
            'updated': dj_timezone.now(),
        }
        entry_args.update((key, adjustments_entry[key]) for key in adjustments_entry.keys())

        Entry.objects.create(**entry_args)

        self.assertEqual(Entry.objects.count(), 1)
        self.assertEqual(Blog.objects.count(), 1)


class TestIndexAnonymous(IndexMixin, TestCase):

    def test_recent_entry_shown(self):
        self._create_blog_with_entry()

        response = self.client.get('/')
        self.assertContains(response, 'This is a test')

    def test_no_article(self):
        response = self.client.get('/')
        self.assertContains(response, 'No articles were aggregated')

    def test_hidden_entry_not_shown(self):
        self._create_blog_with_entry(adjustments_entry={'hidden': True})

        response = self.client.get('/')
        self.assertContains(response, 'No articles were aggregated')

    def test_entry_from_disabled_blog_not_shown(self):
        self._create_blog_with_entry(adjustments_blog={'active': False,})

        response = self.client.get('/')
        self.assertContains(response, 'No articles were aggregated')

    def test_old_entry_not_shown(self):
        old_datetime = datetime.datetime(2010, 1, 1, 15, 55, tzinfo=datetime.timezone.utc)
        self._create_blog_with_entry(adjustments_entry={
            'pub_date': old_datetime,
            'updated': old_datetime,
        })

        response = self.client.get('/')
        self.assertContains(response, 'No articles were aggregated')

    def test_cache(self):
        with self.assertNumQueries(8):
            self.client.get('/')

        with self.assertNumQueries(1):
            self.client.get('/')

        self.assertTrue(cache.has_key('inyoka:planet:views:index:anonymous'))


class TestIndexAuthenticated(TestIndexAnonymous):

    def setUp(self):
        super().setUp()
        self.client.login(username='user', password='user')

    def test_cache(self):
        """Should not use any planet cache for authenticated users."""
        with self.assertNumQueries(8):
            self.client.get('/')

        with self.assertNumQueries(5):
            self.client.get('/')

        self.assertFalse(cache.has_key('inyoka:planet:views:index:anonymous'))


class TestIndexPrivileged(IndexMixin, TestCase):

    def setUp(self):
        super().setUp()
        self._assign_user_privileges()
        self.client.login(username='user', password='user')

    def test_recent_entry_shown(self):
        self._create_blog_with_entry()

        response = self.client.get('/')
        self.assertContains(response, 'This is a test')

    def test_no_article(self):
        response = self.client.get('/')
        self.assertContains(response, 'No articles were aggregated')

    def test_hidden_entry_shown(self):
        self._create_blog_with_entry(adjustments_entry={'hidden': True})

        response = self.client.get('/')
        self.assertContains(response, 'This is a test')

    def test_entry_from_disabled_shown(self):
        self._create_blog_with_entry(adjustments_blog={'active': False,})

        response = self.client.get('/')
        self.assertContains(response, 'This is a test')

    def test_old_entry_shown(self):
        old_datetime = datetime.datetime(2010, 1, 1, 15, 55, tzinfo=datetime.timezone.utc)
        self._create_blog_with_entry(adjustments_entry={
            'pub_date': old_datetime,
            'updated': old_datetime,
        })

        response = self.client.get('/')
        self.assertContains(response, 'This is a test')

    def test_hide_button_shown(self):
        self._create_blog_with_entry()

        response = self.client.get('/')
        self.assertContains(response, 'Hide')


class TestArchiveIndexViewAnonymous(IndexMixin, TestCase):

    def test_no_article(self):
        response = self.client.get("/archive/")
        self.assertContains(response, 'No articles were aggregated')

    @freeze_time('2013-1-11 11:11')
    def test_recent_entry_shown(self):
        self._create_blog_with_entry()

        response = self.client.get("/archive/")
        self.assertContains(response, f'http://planet.{settings.BASE_DOMAIN_NAME}/2013/week/2/')

    def test_hidden_entry_not_shown(self):
        self._create_blog_with_entry(adjustments_entry={'hidden': True})

        response = self.client.get("/archive/")
        self.assertContains(response, 'No articles were aggregated')

    def test_entry_from_disabled_blog_not_shown(self):
        self._create_blog_with_entry(adjustments_blog={'active': False,})

        response = self.client.get("/archive/")
        self.assertContains(response, 'No articles were aggregated')

    def test_old_entry_not_shown(self):
        old_datetime = datetime.datetime(2010, 1, 1, 15, 55, tzinfo=datetime.timezone.utc)
        self._create_blog_with_entry(adjustments_entry={
            'pub_date': old_datetime,
            'updated': old_datetime,
        })

        response = self.client.get("/archive/")
        self.assertContains(response, 'No articles were aggregated')


class TestArchiveIndexViewAuthenticated(TestArchiveIndexViewAnonymous):

    def setUp(self):
        super().setUp()
        self.client.login(username='user', password='user')


class TestArchiveIndexViewPrivileged(IndexMixin, TestCase):

    def setUp(self):
        super().setUp()
        self._assign_user_privileges()
        self.client.login(username='user', password='user')

    def test_no_article(self):
        response = self.client.get("/archive/")
        self.assertContains(response, 'No articles were aggregated')

    @freeze_time('2013-1-11 11:11')
    def test_recent_entry_shown(self):
        self._create_blog_with_entry()

        response = self.client.get("/archive/")
        self.assertContains(response, f'http://planet.{settings.BASE_DOMAIN_NAME}/2013/week/2/')

    @freeze_time('2013-1-11 11:11')
    def test_hidden_entry_shown(self):
        self._create_blog_with_entry(adjustments_entry={'hidden': True})

        response = self.client.get("/archive/")
        self.assertContains(response, f'http://planet.{settings.BASE_DOMAIN_NAME}/2013/week/2/')

    @freeze_time('2013-1-11 11:11')
    def test_entry_from_disabled_blog_shown(self):
        self._create_blog_with_entry(adjustments_blog={'active': False,})

        response = self.client.get("/archive/")
        self.assertContains(response, f'http://planet.{settings.BASE_DOMAIN_NAME}/2013/week/2/')

    def test_old_entry_shown(self):
        old_datetime = datetime.datetime(2010, 1, 1, 15, 55, tzinfo=datetime.timezone.utc)
        self._create_blog_with_entry(adjustments_entry={
            'pub_date': old_datetime,
            'updated': old_datetime,
        })

        response = self.client.get("/archive/")
        self.assertContains(response,
                            f'http://planet.{settings.BASE_DOMAIN_NAME}/2009/week/53/')


class BaseTestEntryWeekArchiveView(IndexMixin):

    def test_no_article(self):
        response = self.client.get("/2020/week/12/")
        self.assertEqual(response.status_code, 404)

    def test_entry_shown(self):
        old_datetime = datetime.datetime(2013, 1, 10, 15, 55, tzinfo=datetime.timezone.utc)
        self._create_blog_with_entry(adjustments_entry={
            'pub_date': old_datetime,
            'updated': old_datetime,
        })

        response = self.client.get("/2013/week/2/")
        self.assertContains(response, 'testTitle')

        response = self.client.get("/2013/week/1/")
        self.assertEqual(response.status_code, 404)
        response = self.client.get("/2013/week/3/")
        self.assertEqual(response.status_code, 404)


@freeze_time('2013-1-11 11:11')
class TestEntryWeekArchiveViewAnonymous(BaseTestEntryWeekArchiveView, TestCase):

    def test_hidden_entry_not_shown(self):
        self._create_blog_with_entry(adjustments_entry={'hidden': True})

        response = self.client.get("/2013/week/2/")
        self.assertEqual(response.status_code, 404)

    def test_entry_from_disabled_blog_not_shown(self):
        self._create_blog_with_entry(adjustments_blog={'active': False,})

        response = self.client.get("/2013/week/2/")
        self.assertEqual(response.status_code, 404)

    def test_old_entry_not_shown(self):
        old_datetime = datetime.datetime(2000, 1, 3, 15, 55, tzinfo=datetime.timezone.utc)
        self._create_blog_with_entry(adjustments_entry={
            'pub_date': old_datetime,
            'updated': old_datetime,
        })

        with freeze_time('2003-1-11 11:11'):
            response = self.client.get("/2000/week/1/")
            self.assertEqual(response.status_code, 200)

        response = self.client.get("/2000/week/1/")
        self.assertEqual(response.status_code, 404)


class TestEntryWeekArchiveViewAuthenticated(TestEntryWeekArchiveViewAnonymous):

    def setUp(self):
        super().setUp()
        self.client.login(username='user', password='user')


@freeze_time('2013-1-11 11:11')
class TestEntryWeekArchiveViewPrivileged(BaseTestEntryWeekArchiveView, TestCase):

    def setUp(self):
        super().setUp()

        self._assign_user_privileges()
        self.client.login(username='user', password='user')

    def test_hidden_entry_shown(self):
        """
        With a privilege the post should still be shown for this user.
        Thus, it is also possible to unhide it.
        """
        self._create_blog_with_entry(adjustments_entry={'hidden': True})

        response = self.client.get("/2013/week/2/")
        self.assertContains(response, 'This is a test')
        self.assertContains(response, 'Restore')

    def test_entry_from_disabled_blog_shown(self):
        """
        With a privilege the post should still be shown for this user.
        """
        self._create_blog_with_entry(adjustments_blog={'active': False,})

        response = self.client.get("/2013/week/2/")
        self.assertEqual(response.status_code, 200)

    def test_old_entry_shown(self):
        old_datetime = datetime.datetime(2000, 1, 3, 15, 55, tzinfo=datetime.timezone.utc)
        self._create_blog_with_entry(adjustments_entry={
            'pub_date': old_datetime,
            'updated': old_datetime,
        })

        response = self.client.get("/2000/week/1/")
        self.assertEqual(response.status_code, 200)

    def test_hide_button_shown(self):
        self._create_blog_with_entry()

        response = self.client.get("/2013/week/2/")
        self.assertContains(response, 'Hide')


class TestSuggestView(TestCase):
    client_class = InyokaClient

    def setUp(self):
        super().setUp()
        self.admin = User.objects.register_user('admin', 'admin', 'admin', False)
        self.admin.is_superuser = True
        self.admin.save()

        self.client.defaults['HTTP_HOST'] = 'planet.%s' % settings.BASE_DOMAIN_NAME
        self.client.login(username='admin', password='admin')

    def test_status_code(self):
        response = self.client.get('/suggest/')
        self.assertEqual(response.status_code, 200)

    def test_abort(self):
        response = self.client.post('/suggest/', data={'abort': True}, follow=True)
        self.assertRedirects(response, href('planet'))

    def test_submit_suggestion(self):
        ikhaya_team_member = User.objects.register_user(
            'ikm', 'ikm@inyoka.local', 'ikm', False
        )
        ikhaya_team_member2 = User.objects.register_user(
            'ikm2', 'ikm2@inyoka.local', 'ikm2', False
        )

        group = Group.objects.get(name__iexact=settings.INYOKA_IKHAYA_GROUP_NAME)
        ikhaya_team_member.groups.add(group)
        ikhaya_team_member2.groups.add(group)

        data = {
            'name': 'Testblog',
            'url': 'http://inyoka.test/',
            'description': 'Description of the Testblog',
        }

        response = self.client.post('/suggest/', data=data, follow=True)
        self.assertRedirects(response, href('planet'))
        self.assertContains(response, 'was suggested.')

        self.assertEqual(len(mail.outbox), 2)
        for m in mail.outbox:
            self.assertIn('was suggested.', m.subject)
            self.assertIn(
                m.to[0], [ikhaya_team_member.email, ikhaya_team_member2.email]
            )

    def test_submit_suggestion__no_team_member(self):
        data = {
            'name': 'Testblog',
            'url': 'http://inyoka.test/',
            'description': 'Description of the Testblog',
        }

        response = self.client.post('/suggest/', data=data, follow=True)
        self.assertRedirects(response, href('planet'))
        self.assertContains(
            response, 'No user is registered as a planet administrator.'
        )
