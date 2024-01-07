"""
    tests.apps.ikhaya.test_views
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test Ikhaya views.

    :copyright: (c) 2012-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import datetime
import zoneinfo

import feedparser
from django.conf import settings
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory
from django.utils.dateparse import parse_datetime
from freezegun import freeze_time
from guardian.shortcuts import assign_perm

from inyoka.ikhaya.models import Article, Category, Comment, Report, Suggestion
from inyoka.ikhaya.views import events
from inyoka.portal.user import User
from inyoka.utils.storage import storage
from inyoka.utils.test import InyokaClient, TestCase
from inyoka.utils.urls import href


class TestViews(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()
        self.admin = User.objects.register_user('admin', 'admin', 'admin', False)
        self.user = User.objects.register_user('user', 'user', 'user', False)
        self.admin.is_superuser = True
        self.admin.save()

        self.cat = Category.objects.create(name="Categrory")
        self.article = Article.objects.create(author=self.admin, subject="Subject",
                            text="Text", pub_date=datetime.datetime.today().date(),
                            pub_time=datetime.datetime.now().time(), category=self.cat)
        self.comment = Comment.objects.create(article=self.article, text="Text",
                            author=self.user, pub_date=datetime.datetime.now())
        self.report = Report.objects.create(article=self.article, text="Text",
                            author=self.user, pub_date=datetime.datetime.now())

        self.client.defaults['HTTP_HOST'] = 'ikhaya.%s' % settings.BASE_DOMAIN_NAME
        self.client.login(username='admin', password='admin')

    def test_comment_update(self):
        self.assertEqual(Comment.objects.get(id=self.comment.id).deleted, False)

        self.client.post('/comment/%d/hide/' % self.comment.id, {'cancel': True})
        self.assertEqual(Comment.objects.get(id=self.comment.id).deleted, False)

        self.client.post('/comment/%d/hide/' % self.comment.id, {'confirm': True})
        self.assertEqual(Comment.objects.get(id=self.comment.id).deleted, True)

        self.client.post('/comment/%d/restore/' % self.comment.id, {'cancel': True})
        self.assertEqual(Comment.objects.get(id=self.comment.id).deleted, True)

        self.client.post('/comment/%d/restore/' % self.comment.id, {'confirm': True})
        self.assertEqual(Comment.objects.get(id=self.comment.id).deleted, False)

    def test_report_deleted_update(self):
        self.assertEqual(Report.objects.get(id=self.report.id).deleted, False)

        self.client.post('/report/%d/hide/' % self.report.id, {'cancel': True})
        self.assertEqual(Report.objects.get(id=self.report.id).deleted, False)

        self.client.post('/report/%d/hide/' % self.report.id, {'confirm': True})
        self.assertEqual(Report.objects.get(id=self.report.id).deleted, True)

        self.client.post('/report/%d/restore/' % self.report.id, {'cancel': True})
        self.assertEqual(Report.objects.get(id=self.report.id).deleted, True)

        self.client.post('/report/%d/restore/' % self.report.id, {'confirm': True})
        self.assertEqual(Report.objects.get(id=self.report.id).deleted, False)

    def test_report_solved_update(self):
        self.assertEqual(Report.objects.get(id=self.report.id).solved, False)

        self.client.post('/report/%d/solve/' % self.report.id, {'cancel': True})
        self.assertEqual(Report.objects.get(id=self.report.id).solved, False)

        self.client.post('/report/%d/solve/' % self.report.id, {'confirm': True})
        self.assertEqual(Report.objects.get(id=self.report.id).solved, True)

        self.client.post('/report/%d/unsolve/' % self.report.id, {'cancel': True})
        self.assertEqual(Report.objects.get(id=self.report.id).solved, True)

        self.client.post('/report/%d/unsolve/' % self.report.id, {'confirm': True})
        self.assertEqual(Report.objects.get(id=self.report.id).solved, False)

    def test_ticket_854(self):
        user_w = User.objects.register_user('user_w', 'user_w', 'user', False)
        user_w.avatar = "test/path/to/avatarimage.png"
        user_w.save()

        user_wo = User.objects.register_user('user_wo', 'user_wo', 'user', False)

        user_g = User.objects.register_user('user_g', 'user_g', 'user', False)
        user_g.settings['use_gravatar'] = True
        user_g.save()

        avatar_url = href('media', user_w.avatar)
        gravatar_url_part = 'https://www.gravatar.com/avatar/ca39ffdca4bd97c3a6c29a4c8f29b7dc'

        a = Article.objects.create(author=self.admin, subject="Subject 2",
                            text="Text 3", pub_date=datetime.datetime.today().date(),
                            pub_time=datetime.datetime.now().time(), category=self.cat)
        for u in (user_w, user_wo, user_g):
            Comment.objects.create(article=a, text="Comment by %s" % u.username,
                            author=u, pub_date=datetime.datetime.now())

        response = self.client.get("/%s/%s" % (a.stamp, a.slug), follow=True)
        self.assertContains(response, avatar_url, count=1)
        self.assertContains(response, '''<td class="author">
            <p class="username">
                <a href="%s">user_wo</a>
            </p>
        </td>''' % user_wo.get_absolute_url(action='show'), count=1, html=True)
        self.assertContains(response, gravatar_url_part, count=1)
        self.assertContains(response, '<td class="author">', count=3)

    def test_add_event_without_data(self):
        response = self.client.post('/event/suggest/', {'confirm': True})
        self.assertContains(response, 'date<ul class="errorlist">', 1)
        self.assertContains(response, 'name<ul class="errorlist">', 1)
        self.assertContains(response, 'errorlist', 3)

    def test_add_event_without_name(self):
        response = self.client.post('/event/suggest/', {'date': datetime.date(2015, 5, 1),
                                                        'enddate': datetime.date(2015, 5, 2),
                                                        'confirm': True})
        self.assertContains(response, 'name<ul class="errorlist"', 1)
        self.assertContains(response, 'errorlist', 2)

    def test_add_event_with_name_startdate_enddate(self):
        response = self.client.post('/event/suggest/', {'date': datetime.date(2015, 5, 1),
                                                        'enddate': datetime.date(2015, 5, 2),
                                                        'name': 'TestEvent',
                                                        'confirm': True})
        self.assertEqual(response.status_code, 302)

    def test_add_event_with_name_enddate_before_startdate(self):
        response = self.client.post('/event/suggest/', {'date': datetime.date(2015, 6, 1),
                                                        'enddate': datetime.date(2015, 5, 2),
                                                        'name': 'TestEvent',
                                                        'confirm': True})
        self.assertContains(response, 'enddate<ul class="errorlist">', 1)
        self.assertContains(response, 'errorlist', 2)

    def test_add_event_with_name_and_startdate(self):
        response = self.client.post('/event/suggest/', {'date': datetime.date(2015, 6, 1),
                                                        'name': 'TestEvent',
                                                        'confirm': True})
        self.assertEqual(response.status_code, 302)

    def test_add_event_with_name_startdatetime_enddatetime_midnight(self):
        response = self.client.post('/event/suggest/', {'date': datetime.date(2015, 5, 1),
                                                        'time': datetime.time(0, 0, 0),
                                                        'enddate': datetime.date(2015, 5, 2),
                                                        'endtime': datetime.time(0, 0, 0),
                                                        'name': 'TestEvent',
                                                        'confirm': True})
        self.assertEqual(response.status_code, 302)

    def test_add_event_with_name_startdatetime_enddatetime(self):
        response = self.client.post('/event/suggest/', {'date': datetime.date(2015, 5, 1),
                                                        'time': datetime.time(10, 0, 0),
                                                        'enddate': datetime.date(2015, 5, 2),
                                                        'endtime': datetime.time(11, 0, 0),
                                                        'name': 'TestEvent',
                                                        'confirm': True})
        self.assertEqual(response.status_code, 302)

    def test_add_event_with_name_enddatetime_before_startdatetime(self):
        response = self.client.post('/event/suggest/', {'date': datetime.date(2015, 5, 1),
                                                        'time': datetime.time(10, 0, 0),
                                                        'enddate': datetime.date(2015, 5, 1),
                                                        'endtime': datetime.time(9, 0, 0),
                                                        'name': 'TestEvent',
                                                        'confirm': True})
        self.assertContains(response, 'endtime<ul class="errorlist">', 1)
        self.assertContains(response, 'errorlist', 2)


class TestEventView(TestCase):

    client_class = InyokaClient

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.register_user('test', 'test@example.local', password='test', send_mail=False)
        group = Group.objects.create(name='test_event_group')
        assign_perm('portal.change_event', group)
        group.user_set.add(self.user)

        self.client.defaults['HTTP_HOST'] = 'ikhaya.%s' % settings.BASE_DOMAIN_NAME
        self.client.login(username='test', password='test')

    def test_user_can_view_it(self):
        response = self.client.get('/events/')
        self.assertEqual(response.status_code, 200)

    def test_anonymous_gets_error(self):
        request = self.factory.get('/')
        request.user = User.objects.get_anonymous_user()
        with self.assertRaises(PermissionDenied):
            events(request)

    def test_queries_needed(self):
        with self.assertNumQueries(10):
            self.client.get('/events/')


class TestServices(TestCase):

    client_class = InyokaClient
    url = "/?__service__=ikhaya.change_suggestion_assignment"

    def test_post_misses_username(self):
        response = self.client.post(self.url, data={"suggestion": 1})
        self.assertEqual(response.status_code, 400)

    def test_post_misses_suggestion_id(self):
        response = self.client.post(self.url, data={"username": "foo"})
        self.assertEqual(response.status_code, 400)

    def test_set_owner(self):
        user = User.objects.register_user('test', 'test@example.local', password='test', send_mail=False)
        suggestion = Suggestion.objects.create(author=user, title='title', text='text', intro='intro', notes='notes')
        self.assertIsNone(suggestion.owner)

        self.client.post(self.url, data={"username": user.username, "suggestion": suggestion.id})
        suggestion.refresh_from_db()
        self.assertEqual(suggestion.owner_id, user.id)

        self.client.post(self.url, data={"username": "-", "suggestion": suggestion.id})
        suggestion.refresh_from_db()
        self.assertIsNone(suggestion.owner)

    def test_invalid_owner(self):
        suggestion = Suggestion.objects.create(
            author=User.objects.get_anonymous_user(), title='title', text='text', intro='intro', notes='notes')

        response = self.client.post(self.url, data={"username": "foo", "suggestion": suggestion.id})
        self.assertEqual(response.status_code, 404)

    def test_invalid_suggestion(self):
        user = User.objects.register_user('test', 'test@example.local', password='test', send_mail=False)

        response = self.client.post(self.url, data={"username": user.username, "suggestion": 4242})
        self.assertEqual(response.status_code, 404)


@freeze_time("2023-12-09T23:55:04Z")
class TestArticleFeeds(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()

        self.now = datetime.datetime.now().replace(microsecond=0)
        now = self.now
        today = now.date()
        time_now = now.time()

        self.admin = User.objects.register_user('admin', 'admin', 'admin', False)
        self.user = User.objects.register_user('user', 'user', 'user', False)
        self.admin.is_superuser = True
        self.admin.save()

        self.cat = Category.objects.create(name="Category")
        self.article = Article.objects.create(author=self.admin, subject="Subject",
                            text="Text", pub_date=today,
                            pub_time=time_now, category=self.cat, public=True)
        self.comment = Comment.objects.create(article=self.article, text="Text",
                            author=self.user, pub_date=now)

        self.client.defaults['HTTP_HOST'] = 'ikhaya.%s' % settings.BASE_DOMAIN_NAME

    def test_modes(self):
        response = self.client.get('/feeds/short/10/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/feeds/title/20/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/feeds/full/50/')
        self.assertEqual(response.status_code, 200)

    def test_queries(self):
        with self.assertNumQueries(4):
            self.client.get('/feeds/full/50/')

    def test_multiple_articles(self):
        today = self.now.date()
        time_now = self.now.time()

        self.article = Article.objects.create(author=self.admin, subject="Subject 2",
                            text="Text 2", pub_date=today,
                            pub_time=time_now, category=self.cat, public=True)

        response = self.client.get('/feeds/full/10/')
        self.assertIn(self.article.subject, response.content.decode())

        feed = feedparser.parse(response.content)
        self.assertEqual(len(feed.entries), 2)

    def test_content_exact(self):
        storage['ikhaya_description_rendered'] = 'Just to describe ikhaya'

        response = self.client.get('/feeds/full/10/')

        self.maxDiff = None
        self.assertXMLEqual(response.content.decode(),
'''<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="en-us">
  <title>ubuntuusers.local:8080 Ikhaya</title>
  <link href="http://ikhaya.ubuntuusers.local:8080/" rel="alternate"/>
  <link href="http://ikhaya.ubuntuusers.local:8080/feeds/full/10/" rel="self" />
  <id>http://ikhaya.ubuntuusers.local:8080/</id>
  <updated>2023-12-10T00:55:04+01:00</updated>
  <subtitle>Just to describe ikhaya</subtitle>
  <rights>http://ubuntuusers.local:8080/lizenz/</rights>
  <entry>
    <title>Subject</title>
    <link href="http://ikhaya.ubuntuusers.local:8080/2023/12/09/subject/" rel="alternate"/>
    <published>2023-12-10T00:55:04+01:00</published>
    <updated>2023-12-10T00:55:04+01:00</updated>
    <author>
      <name>admin</name>
      <uri>http://ubuntuusers.local:8080/user/admin/</uri>
    </author>
    <id>http://ikhaya.ubuntuusers.local:8080/2023/12/09/subject/</id>
    <summary type="html">
&lt;p&gt;Text&lt;/p&gt;</summary>
    <category term="Category"/>
  </entry>
</feed>
''')

    def test_content_displayed(self):
        storage['ikhaya_description_rendered'] = 'Just to describe ikhaya'

        response = self.client.get('/feeds/full/10/')

        feed = feedparser.parse(response.content)

        # feed properties
        self.assertEqual(feed.feed.title, 'ubuntuusers.local:8080 Ikhaya')
        self.assertEqual(feed.feed.subtitle, 'Just to describe ikhaya')
        self.assertEqual(feed.feed.title_detail.type, 'text/plain')
        self.assertEqual(feed.feed.title_detail.language, 'en-us')
        self.assertEqual(feed.feed.id, 'http://ikhaya.ubuntuusers.local:8080/')
        self.assertEqual(feed.feed.link, 'http://ikhaya.ubuntuusers.local:8080/')

        now_utc = self.now
        now_utc = now_utc.replace(tzinfo=zoneinfo.ZoneInfo("Europe/London"))

        feed_updated = parse_datetime(feed.feed.updated)
        self.assertEqual(feed_updated, now_utc)

        self.assertEqual(feed.feed.rights, href('portal', 'lizenz'))
        self.assertNotIn('author', feed.feed)
        self.assertNotIn('author_detail', feed.feed)

        # entry properties
        self.assertEqual(len(feed.entries), 1)
        entry = feed.entries[0]

        url = f'http://ikhaya.ubuntuusers.local:8080/{self.now.year}/{self.now.month:02d}/{self.now.day:02d}/subject/'
        self.assertEqual(entry.id, url)
        self.assertEqual(entry.link, url)

        self.assertEqual(entry.title_detail.value, 'Subject')
        self.assertEqual(entry.title_detail.type, 'text/plain')
        self.assertEqual(entry.summary, '<p>Text</p>')
        self.assertEqual(entry.summary_detail.type, 'text/html')
        self.assertNotIn('text', entry)
        self.assertNotIn('created_parsed', entry)

        entry_published = parse_datetime(entry.published)
        self.assertEqual(entry_published, now_utc)

        entry_date = parse_datetime(entry.date)
        self.assertEqual(entry_date, now_utc)

        entry_updated = parse_datetime(entry.updated)
        self.assertEqual(entry_updated, now_utc)

        self.assertEqual(entry.author, self.admin.username)
        self.assertEqual(entry.author_detail.name, self.admin.username)
        self.assertEqual(entry.author_detail.href, 'http://ubuntuusers.local:8080/user/admin/')


@freeze_time("2023-12-09T23:55:04Z")
class TestArticleCategoryFeeds(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()

        self.now = datetime.datetime.now().replace(microsecond=0)
        self.today = self.now.date()
        self.time_now = self.now.time()

        self.admin = User.objects.register_user('admin', 'admin', 'admin', False)
        self.user = User.objects.register_user('user', 'user', 'user', False)
        self.admin.is_superuser = True
        self.admin.save()

        self.cat = Category.objects.create(name="Test Category")
        self.article = Article.objects.create(author=self.admin, subject="Subject",
                            text="Text", pub_date=self.today,
                            pub_time=self.time_now, category=self.cat, public=True)

        self.client.defaults['HTTP_HOST'] = 'ikhaya.%s' % settings.BASE_DOMAIN_NAME

        storage['ikhaya_description_rendered'] = 'Just to describe ikhaya'

    def test_modes(self):
        response = self.client.get(f'/feeds/{self.cat.slug}/short/10/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(f'/feeds/{self.cat.slug}/title/20/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(f'/feeds/{self.cat.slug}/full/50/')
        self.assertEqual(response.status_code, 200)

    def test_queries(self):
        with self.assertNumQueries(3):
            self.client.get(f'/feeds/{self.cat.slug}/full/50/')

    def test_multiple_articles(self):
        self.article = Article.objects.create(author=self.admin, subject="Subject 2",
                            text="Text 2", pub_date=self.today,
                            pub_time=self.time_now, category=self.cat, public=True)

        response = self.client.get(f'/feeds/{self.cat.slug}/full/10/')
        self.assertIn(self.article.subject, response.content.decode())

        feed = feedparser.parse(response.content)
        self.assertEqual(len(feed.entries), 2)

    def test_content_exact(self):
        response = self.client.get(f'/feeds/{self.cat.slug}/full/10/')

        Article.objects.create(author=self.admin, subject="Another article in another category",
                               text="Text 2", pub_date=self.today,
                               pub_time=self.time_now, category=Category.objects.create(name="Another"), public=True)

        self.maxDiff = None
        self.assertXMLEqual(response.content.decode(),
'''<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="en-us">
  <title>ubuntuusers.local:8080 Ikhaya – test-category</title>
  <link href="http://ikhaya.ubuntuusers.local:8080/category/test-category/" rel="alternate" />
  <link href="http://ikhaya.ubuntuusers.local:8080/feeds/test-category/full/10/" rel="self" />
  <id>http://ikhaya.ubuntuusers.local:8080/category/test-category/</id>
  <updated>2023-12-10T00:55:04+01:00</updated>
  <subtitle>Just to describe ikhaya</subtitle>
  <rights>http://ubuntuusers.local:8080/lizenz/</rights>
  <entry>
    <title>Subject</title>
    <link href="http://ikhaya.ubuntuusers.local:8080/2023/12/09/subject/" rel="alternate"/>
    <published>2023-12-10T00:55:04+01:00</published>
    <updated>2023-12-10T00:55:04+01:00</updated>
    <author>
      <name>admin</name>
      <uri>http://ubuntuusers.local:8080/user/admin/</uri>
    </author>
    <id>http://ikhaya.ubuntuusers.local:8080/2023/12/09/subject/</id>
    <summary type="html">
&lt;p&gt;Text&lt;/p&gt;</summary>
    <category term="Test Category"/>
  </entry>
</feed>
''')


@freeze_time("2023-12-09T23:55:04Z")
class TestCommentsFeed(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()

        self.now = datetime.datetime.now().replace(microsecond=0)
        self.today = self.now.date()
        self.time_now = self.now.time()

        self.admin = User.objects.register_user('admin', 'admin', 'admin', False)
        self.user = User.objects.register_user('user', 'user', 'user', False)
        self.admin.is_superuser = True
        self.admin.save()

        self.cat = Category.objects.create(name="Test Category")
        self.article = Article.objects.create(author=self.admin, subject="Article Subject",
                            text="Text", pub_date=self.today,
                            pub_time=self.time_now, category=self.cat, public=True)

        self.comment = Comment.objects.create(article=self.article, text="Text",
                            author=self.user, pub_date=self.now)

        self.client.defaults['HTTP_HOST'] = 'ikhaya.%s' % settings.BASE_DOMAIN_NAME

        storage['ikhaya_description_rendered'] = '<em>Just</em> to describe ikhaya'

    def test_modes(self):
        response = self.client.get(f'/feeds/comments/short/10/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(f'/feeds/comments/title/20/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(f'/feeds/comments/full/50/')
        self.assertEqual(response.status_code, 200)

    def test_queries(self):
        with self.assertNumQueries(3):
            self.client.get(f'/feeds/comments/full/50/')

    def test_multiple_comments(self):
        self.comment = Comment.objects.create(article=self.article, text="Some other Text",
                            author=self.user, pub_date=self.now)

        response = self.client.get(f'/feeds/comments/full/10/')
        self.assertIn(self.article.subject, response.content.decode())

        feed = feedparser.parse(response.content)
        self.assertEqual(len(feed.entries), 2)

    def test_content_exact(self):
        response = self.client.get(f'/feeds/comments/full/10/')

        self.maxDiff = None
        self.assertXMLEqual(response.content.decode(),
'''<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="en-us">
  <title>ubuntuusers.local:8080 Ikhaya comments</title>
  <link href="http://ikhaya.ubuntuusers.local:8080/" rel="alternate" />
  <link href="http://ikhaya.ubuntuusers.local:8080/feeds/comments/full/10/" rel="self" />
  <id>http://ikhaya.ubuntuusers.local:8080/</id>
  <updated>2023-12-10T00:55:04+01:00</updated>
  <subtitle>Just to describe ikhaya</subtitle>
  <rights>http://ubuntuusers.local:8080/lizenz/</rights>
  <entry>
    <title>Re: Article Subject</title>
    <link href="http://ikhaya.ubuntuusers.local:8080/2023/12/09/article-subject/#comment_1" rel="alternate"/>
    <published>2023-12-10T00:55:04+01:00</published>
    <updated>2023-12-10T00:55:04+01:00</updated>
    <author>
      <name>user</name>
      <uri>http://ubuntuusers.local:8080/user/user/</uri>
    </author>
    <id>http://ikhaya.ubuntuusers.local:8080/2023/12/09/article-subject/#comment_1</id>
    <summary type="html">&lt;p&gt;Text&lt;/p&gt;</summary>
  </entry>
</feed>
''')


@freeze_time("2023-12-09T23:55:04Z")
class TestCommentsPerArticleFeed(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()

        self.now = datetime.datetime.now().replace(microsecond=0)
        self.today = self.now.date()
        self.time_now = self.now.time()

        self.admin = User.objects.register_user('admin', 'admin', 'admin', False)
        self.user = User.objects.register_user('user', 'user', 'user', False)
        self.admin.is_superuser = True
        self.admin.save()

        self.cat = Category.objects.create(name="Test Category")
        self.article = Article.objects.create(author=self.admin, subject="Article Subject",
                            text="Text", pub_date=self.today,
                            pub_time=self.time_now, category=self.cat, public=True, id=1)

        self.comment = Comment.objects.create(article=self.article, text="Text",
                            author=self.user, pub_date=self.now)

        self.client.defaults['HTTP_HOST'] = 'ikhaya.%s' % settings.BASE_DOMAIN_NAME

        storage['ikhaya_description_rendered'] = 'Just to describe ikhaya'

    def test_modes(self):
        response = self.client.get(f'/feeds/comments/{self.article.id}/short/10/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(f'/feeds/comments/{self.article.id}/title/20/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(f'/feeds/comments/{self.article.id}/full/50/')
        self.assertEqual(response.status_code, 200)

    def test_queries(self):
        with self.assertNumQueries(4):
            self.client.get(f'/feeds/comments/{self.article.id}/full/50/')

    def test_multiple_comments(self):
        self.comment = Comment.objects.create(article=self.article, text="Some other Text",
                            author=self.user, pub_date=self.now)

        response = self.client.get(f'/feeds/comments/{self.article.id}/full/10/')
        self.assertIn(self.article.subject, response.content.decode())

        feed = feedparser.parse(response.content)
        self.assertEqual(len(feed.entries), 2)

    def test_content_exact(self):
        response = self.client.get(f'/feeds/comments/{self.article.id}/full/10/')

        self.maxDiff = None
        self.assertXMLEqual(response.content.decode(),
'''<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="en-us">
  <title>ubuntuusers.local:8080 Ikhaya comments – Article Subject</title>
  <link href="http://ikhaya.ubuntuusers.local:8080/2023/12/09/article-subject/" rel="alternate"/>
  <link href="http://ikhaya.ubuntuusers.local:8080/feeds/comments/1/full/10/" rel="self" />
  <id>http://ikhaya.ubuntuusers.local:8080/2023/12/09/article-subject/</id>
  <updated>2023-12-10T00:55:04+01:00</updated>
  <subtitle>Just to describe ikhaya</subtitle>
  <rights>http://ubuntuusers.local:8080/lizenz/</rights>
  <entry>
    <title>Re: Article Subject</title>
    <link href="http://ikhaya.ubuntuusers.local:8080/2023/12/09/article-subject/#comment_1" rel="alternate"/>
    <published>2023-12-10T00:55:04+01:00</published>
    <updated>2023-12-10T00:55:04+01:00</updated>
    <author>
      <name>user</name>
      <uri>http://ubuntuusers.local:8080/user/user/</uri>
    </author>
    <id>http://ikhaya.ubuntuusers.local:8080/2023/12/09/article-subject/#comment_1</id>
    <summary type="html">&lt;p&gt;Text&lt;/p&gt;</summary>
  </entry>
</feed>
''')
