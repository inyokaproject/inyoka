"""
    tests.apps.wiki.test_views
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test wiki views.

    :copyright: (c) 2012-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime, timedelta
from unittest.mock import patch

import feedparser
from django.conf import settings
from django.test.utils import override_settings
from freezegun import freeze_time

from inyoka.portal.user import User
from inyoka.utils.sessions import SurgeProtectionMixin
from inyoka.utils.test import InyokaClient, TestCase
from inyoka.utils.urls import href
from inyoka.wiki.models import Page
from inyoka.wiki.storage import storage


class TestViews(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()
        self.admin = User.objects.register_user('admin', 'admin', 'admin', False)
        self.client.defaults['HTTP_HOST'] = 'wiki.%s' % settings.BASE_DOMAIN_NAME
        self.client.login(username='admin', password='admin')

    @override_settings(WIKI_REVISIONS_PER_PAGE=5)
    def test_log(self):
        p50 = Page.objects.create('Testpage50', 'rev 0', user=self.admin, note='rev 0')
        p100 = Page.objects.create('Testpage100', 'rev 0', user=self.admin, note='rev 0')
        p250 = Page.objects.create('Testpage250', 'rev 0', user=self.admin, note='rev 0')

        for i in range(1, 2):
            p50.edit(text='rev %d' % i, user=self.admin, note='rev %d' % i)
        p50.save()

        for i in range(1, 5):
            p100.edit(text='rev %d' % i, user=self.admin, note='rev %d' % i)
        p100.save()

        for i in range(1, 12):
            p250.edit(text='rev %d' % i, user=self.admin, note='rev %d' % i)
        p250.save()

        req = self.client.get("/Testpage50/a/log", follow=True).content
        self.assertEqual(req.count(b'<tr'), 2)
        req = self.client.get("/Testpage50/a/log/2", follow=True)
        self.assertEqual(req.status_code, 404)

        req = self.client.get("/Testpage100/a/log", follow=True).content
        self.assertEqual(req.count(b'<tr'), 5)
        req = self.client.get("/Testpage100/a/log/2", follow=True)
        self.assertEqual(req.status_code, 404)

        req = self.client.get("/Testpage250/a/log", follow=True).content
        self.assertEqual(req.count(b'<tr'), 5)
        req = self.client.get("/Testpage250/a/log/2", follow=True).content
        self.assertEqual(req.count(b'<tr'), 5)
        req = self.client.get("/Testpage250/a/log/3", follow=True).content
        self.assertEqual(req.count(b'<tr'), 2)
        req = self.client.get("/Testpage250/a/log/4", follow=True)
        self.assertEqual(req.status_code, 404)


class TestDoCreate(TestCase):

    client_class = InyokaClient

    surge_protection_message = SurgeProtectionMixin.surge_protection_message

    def setUp(self):
        super().setUp()
        self.user = User.objects.register_user('user', 'user@example.test', 'user', False)

        self.client.login(username='user', password='user')
        self.client.defaults['HTTP_HOST'] = 'wiki.%s' % settings.BASE_DOMAIN_NAME
        self.url = href('wiki', 'wiki', 'create')

        storage.clear_cache()

    def test_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_simple_create(self):
        self.client.post(self.url, data={'name': 'newpage', 'template': ''})

        self.assertEqual(Page.objects.get().name, 'newpage')

    def test_normalization_create(self):
        self.client.post(self.url, data={'name': 'new page', 'template': ''})

        self.assertEqual(Page.objects.get().name, 'new_page')

    def test_error_with_different_pagename_case(self):
        Page.objects.create(user=self.user, name='abc', remote_addr='', text='test')

        response = self.client.post(self.url, data={'name': 'Abc', 'template': ''})

        self.assertEqual(Page.objects.count(), 1)
        self.assertContains(response, 'The page Abc already exists.')

    def _create_page(self, name):
            return self.client.post(self.url, data={'name': name, 'template': ''}, follow=True)

    @patch('inyoka.portal.models.User.is_team_member', False)
    def test_surge_protection(self):
        response = self._create_page('p1')
        self.assertNotContains(response, self.surge_protection_message)

        response = self._create_page('should_timeout')
        self.assertContains(response, self.surge_protection_message)

    @patch('inyoka.portal.models.User.is_team_member', True)
    def test_surge_protection__not_affects_team_member(self):
        response = self._create_page('p1')
        self.assertNotContains(response, self.surge_protection_message)

        response = self._create_page('no_timeout')
        self.assertNotContains(response, self.surge_protection_message)


class TestDoEdit(TestCase):

    client_class = InyokaClient

    surge_protection_message = SurgeProtectionMixin.surge_protection_message

    def setUp(self):
        super().setUp()
        self.user = User.objects.register_user('user', 'user@example.test', 'user', False)

        self.client.login(username='user', password='user')
        self.client.defaults['HTTP_HOST'] = 'wiki.%s' % settings.BASE_DOMAIN_NAME

        self.page = Page.objects.create(user=self.user, name='abc', remote_addr='', text='test')
        self.url = self.page.get_absolute_url('edit')

    def _edit_page(self, new_content):
        data = {'text': new_content, 'note': new_content, 'edit_time': datetime.utcnow(),
                'revision': self.page.last_rev_id}
        return self.client.post(self.url, data=data, follow=True)

    @patch('inyoka.portal.models.User.is_team_member', False)
    def test_surge_protection(self):
        response = self._edit_page('p1')
        self.assertNotContains(response, self.surge_protection_message)

        response = self._edit_page('should_timeout')
        self.assertContains(response, self.surge_protection_message)

    @patch('inyoka.portal.models.User.is_team_member', True)
    def test_surge_protection__not_affects_team_member(self):
        response = self._edit_page('p1')
        self.assertNotContains(response, self.surge_protection_message)

        response = self._edit_page('no_timeout')
        self.assertNotContains(response, self.surge_protection_message)


class TestDoShow(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()
        self.user = User.objects.register_user('user', 'user@example.test', 'user', False)

        self.page_name = 'test_page'
        page = Page.objects.create(user=self.user, name=self.page_name, remote_addr='', text=self.page_name)
        self.url = page.get_absolute_url('show')

        self.client.login(username='user', password='user')
        self.client.defaults['HTTP_HOST'] = 'wiki.%s' % settings.BASE_DOMAIN_NAME

    def test_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_no_existing_revision(self):
        p = Page.objects.get_by_name(self.page_name)
        url = p.get_absolute_url(revision=123456)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_redirect(self):
        text = f'# X-Redirect: {self.page_name}\nfoobar content'
        redirect = Page.objects.create(user=self.user, name='redirect', remote_addr='', text=text)

        response = self.client.get(redirect.get_absolute_url('show'), follow=True)
        self.assertRedirects(response, self.url)
        self.assertContains(
            response,
            '<a href="http://wiki.ubuntuusers.local:8080/redirect/no_redirect/">redirect</a>',
            html=True
        )

    def test_redirect_loop(self):
        name = 'redirect'
        text = f'# X-Redirect: {name}\nfoobar content'
        redirect = Page.objects.create(user=self.user, name=name, remote_addr='', text=text)

        response = self.client.get(redirect.get_absolute_url('show'), follow=True)
        self.assertRedirects(response, redirect.get_absolute_url('show_no_redirect'))

    def test_view_old_revision(self):
        p = Page.objects.get_by_name(self.page_name)
        old_rev = p.last_rev_id
        p.edit(text='foo', user=self.user)

        url = p.get_absolute_url('revision', old_rev)
        response = self.client.get(url, follow=True)
        self.assertContains(
            response,
            'You are viewing an old revision of this wiki page.'
        )

    def test_deleted_page(self):
        p = Page.objects.get_by_name(self.page_name)
        p.edit(user=self.user, deleted=True, note='deleted')

        response = self.client.get(p.get_absolute_url('show'), follow=True)
        self.assertEqual(response.status_code, 404)


class TestDoMetaExport(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()
        user = User.objects.register_user('user', 'user@example.test', 'user', False)

        page_name = 'test_page'
        Page.objects.create(user=user, name=page_name, remote_addr='', text=page_name)
        self.url = href('wiki', page_name, 'a', 'export', 'meta')

        self.client.login(username='user', password='user')
        self.client.defaults['HTTP_HOST'] = 'wiki.%s' % settings.BASE_DOMAIN_NAME

    def test_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        # would need a celery task to run, to contain any content
        self.assertEqual(b'', response.content)

    def test_missing_page(self):
        response = self.client.get(href('wiki', 'not_existing', 'a', 'export', 'meta'))
        self.assertEqual(response.status_code, 404)


class TestDoDiff(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()
        self.user = User.objects.register_user('user', 'user@example.test', 'user', False)

        self.page_name = 'test_page'
        self.page = Page.objects.create(user=self.user, name=self.page_name, remote_addr='', text=self.page_name)
        self.page.edit(text='new text', user=self.user)

        self.client.login(username='user', password='user')
        self.client.defaults['HTTP_HOST'] = 'wiki.%s' % settings.BASE_DOMAIN_NAME

    def test_diff__no_param(self):
        url = self.page.get_absolute_url('diff')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_udiff__no_param(self):
        url = self.page.get_absolute_url('udiff')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, b')\n@@ -1 +1 @@\n-test_page\n+new text')

    def test_diff__only_old_revision(self):
        url = self.page.get_absolute_url('diff', revision=Page.objects.get_head(self.page_name, -1))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_udiff__only_old_revision(self):
        url = self.page.get_absolute_url('udiff', revision=Page.objects.get_head(self.page_name, -1))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, b')\n@@ -1 +1 @@\n-test_page\n+new text')

    def test_diff__two_revisions(self):
        self.page.edit(text='new text #2', user=self.user)
        url = self.page.get_absolute_url(
            'diff',
            revision=Page.objects.get_head(self.page_name, -2),
            new_revision=Page.objects.get_head(self.page_name, 0)
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_udiff__two_revisions(self):
        self.page.edit(text='new text #2', user=self.user)
        url = self.page.get_absolute_url(
            'udiff',
            revision=Page.objects.get_head(self.page_name, -2),
            new_revision=Page.objects.get_head(self.page_name, 0)
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, b')\n@@ -1 +1 @@\n-test_page\n+new text #2')

    def test_diff__invalid_new_revision(self):
        url = self.page.get_absolute_url('diff', revision=1, new_revision='1a')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_udiff__invalid_new_revision(self):
        url = self.page.get_absolute_url('udiff', revision=1, new_revision='a')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


@freeze_time("2023-12-09T23:55:04Z")
class TestRevisionFeed(TestCase):

    client_class = InyokaClient
    fixtures = ['wiki_feed.jsonl']

    def setUp(self):
        super().setUp()

        self.user = User.objects.get(username='user')
        self.page = Page.objects.get(id=1)

        self.client.defaults['HTTP_HOST'] = 'wiki.%s' % settings.BASE_DOMAIN_NAME

    def test_multiple_revisions(self):
        self.page.edit(text='another text', user=self.user)

        response = self.client.get('/_feed/10/')
        self.assertIn(self.page.name, response.content.decode())

        feed = feedparser.parse(response.content)
        self.assertEqual(len(feed.entries), 2)

    def test_queries(self):
        with self.assertNumQueries(3):
            self.client.get('/_feed/10/')

    def test_content_exact(self):
        response = self.client.get('/_feed/10/')

        self.maxDiff = None
        self.assertXMLEqual(response.content.decode(),
'''<?xml version="1.0" encoding="utf-8"?>
<feed xml:lang="en-us" xmlns="http://www.w3.org/2005/Atom">
  <title>ubuntuusers.local:8080 wiki – last changes</title>
  <link href="http://wiki.ubuntuusers.local:8080/wiki/recentchanges/" rel="alternate" />
  <link href="http://wiki.ubuntuusers.local:8080/_feed/10/" rel="self" />
  <id>http://wiki.ubuntuusers.local:8080/wiki/recentchanges/</id>
  <updated>2023-12-10T00:55:04+01:00</updated>
  <subtitle>Feed contains revisions of the whole wiki</subtitle>
  <rights>http://ubuntuusers.local:8080/lizenz/</rights>
  <entry>
    <title>user: Created</title>
    <link href="http://wiki.ubuntuusers.local:8080/test_page/a/revision/1/" rel="alternate" />
    <published>2023-12-10T00:55:04+01:00</published>
    <updated>2023-12-10T00:55:04+01:00</updated>
    <author>
      <name>user</name>
      <uri>http://ubuntuusers.local:8080/user/user/</uri>
    </author>
    <id>http://wiki.ubuntuusers.local:8080/test_page/a/revision/1/</id>
    <summary type="html">user edited the article “test page” on 2023-12-10 00:55:04+01:00. Summary: Created</summary>
  </entry>
</feed>
''')


@freeze_time("2023-12-09T23:55:04Z")
class TestArticleRevisionFeed(TestCase):

    client_class = InyokaClient
    fixtures = ['wiki_feed.jsonl']

    def setUp(self):
        super().setUp()

        self.user = User.objects.get(username='user')
        self.page = Page.objects.get(id=1)

        self.client.defaults['HTTP_HOST'] = 'wiki.%s' % settings.BASE_DOMAIN_NAME

    def test_multiple_revisions(self):
        self.page.edit(text='another text', user=self.user)

        response = self.client.get(self.page.get_absolute_url('feed'))
        self.assertIn(self.page.name, response.content.decode())

        feed = feedparser.parse(response.content)
        self.assertEqual(len(feed.entries), 2)

    def test_page_deleted(self):
        self.page.edit(text='another text', user=self.user, deleted=True)
        response = self.client.get(self.page.get_absolute_url('feed'))
        self.assertIn('deleted the', response.content.decode())

        feed = feedparser.parse(response.content)
        self.assertEqual(len(feed.entries), 2)

    def test_edit_from_anonymous_user(self):
        anonymous = User.objects.get_anonymous_user()
        self.page.edit(text='another text', user=anonymous, remote_addr='127.0.0.1')
        self.page.edit(text='another text', user=anonymous, remote_addr='127.0.0.1', deleted=True)

        response = self.client.get(self.page.get_absolute_url('feed'))
        self.assertIn('anonymous user edited', response.content.decode())
        self.assertIn('anonymous user deleted', response.content.decode())

    def test_queries(self):
        with self.assertNumQueries(5):
            self.client.get(self.page.get_absolute_url('feed'))

    def test_tags(self):
        self.page.edit(text='foob text\n\n#tag: view, install, intro',
                       user=self.user,
                       change_date=datetime.utcnow() + timedelta(minutes=11))
        self.page.update_meta()

        response = self.client.get(self.page.get_absolute_url('feed'))
        feed = feedparser.parse(response.content)
        self.assertEqual(len(feed.entries), 2)

        feed_tags = {t.term for t in feed.entries[1]['tags']}
        self.assertEqual(feed_tags, {'view', 'intro', 'install'})

    def test_content_exact(self):
        response = self.client.get(self.page.get_absolute_url('feed'))

        self.maxDiff = None
        self.assertXMLEqual(response.content.decode(),
'''<?xml version="1.0" encoding="utf-8"?>
<feed xml:lang="en-us" xmlns="http://www.w3.org/2005/Atom">
  <title>ubuntuusers.local:8080 wiki – test_page</title>
  <link href="http://wiki.ubuntuusers.local:8080/test_page/" rel="alternate"></link>
  <link href="http://wiki.ubuntuusers.local:8080/test_page/a/feed/" rel="self"></link>
  <id>http://wiki.ubuntuusers.local:8080/test_page/</id>
  <updated>2023-12-10T00:55:04+01:00</updated>
  <subtitle>Feed contains revisions of the wiki page “test_page”.</subtitle>
  <rights>http://ubuntuusers.local:8080/lizenz/</rights>
  <entry>
    <title>user: Created</title>
    <link href="http://wiki.ubuntuusers.local:8080/test_page/a/revision/1/" rel="alternate"></link>
    <published>2023-12-10T00:55:04+01:00</published>
    <updated>2023-12-10T00:55:04+01:00</updated>
    <author>
      <name>user</name>
      <uri>http://ubuntuusers.local:8080/user/user/</uri>
    </author>
    <id>http://wiki.ubuntuusers.local:8080/test_page/a/revision/1/</id>
    <summary type="html">user edited the article “test page” on 2023-12-10 00:55:04+01:00. Summary: Created</summary>
  </entry>
</feed>
''')
