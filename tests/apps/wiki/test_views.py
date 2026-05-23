"""
    tests.apps.wiki.test_views
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test wiki views.

    :copyright: (c) 2012-2026 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime, timedelta, timezone
from os.path import dirname, join
from unittest.mock import patch

import feedparser
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.files import File
from django.http import Http404
from django.test import RequestFactory
from django.test.utils import override_settings
from freezegun import freeze_time

from inyoka.portal.user import User
from inyoka.utils.sessions import SurgeProtectionMixin
from inyoka.utils.test import InyokaClient, TestCase
from inyoka.utils.urls import href
from inyoka.wiki.models import Page
from inyoka.wiki.storage import storage
from inyoka.wiki.views import get_attachment


class TestViews(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()
        self.admin = User.objects.register_user('admin', 'admin', 'admin', False)
        self.client.defaults['HTTP_HOST'] = 'wiki.%s' % settings.BASE_DOMAIN_NAME
        self.client.login(username='admin', password='admin')

    def test_index(self):
        Page.objects.create(settings.WIKI_MAIN_PAGE, 'rev 0', user=self.admin, note='rev 0')

        response = self.client.get('/', follow=True)

        self.assertRedirects(response,
                             f'http://wiki.{settings.BASE_DOMAIN_NAME}/Welcome/')

    def test_index__redirect_with_GET(self):
        Page.objects.create(settings.WIKI_MAIN_PAGE, 'rev 0', user=self.admin, note='rev 0')

        response = self.client.get('/?foo=bar', follow=True)

        self.assertRedirects(response,
                             f'http://wiki.{settings.BASE_DOMAIN_NAME}/Welcome/?foo=bar')

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

    def test_log_with_different_case_in_name(self):
        page_name = 'testPage5'
        Page.objects.create(page_name, 'rev 0', user=self.admin, note='rev 0')

        url = href('wiki', page_name.upper(), 'a', 'log')
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, '/testPage5/a/log/')


class TestGetAttachment(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()
        self.user = User.objects.register_user('user', 'user@example.test', 'user', False)
        self.admin = User.objects.register_user('admin', 'admin@example.test', 'admin', False)

        self.client.login(username='admin', password='admin')
        self.client.defaults['HTTP_HOST'] = 'wiki.%s' % settings.BASE_DOMAIN_NAME

        # Create a page with an attachment
        with open(join(dirname(__file__), 'evil.png'), 'rb') as evil:
            self.page_with_attachment = Page.objects.create(
                user=self.user,
                text='text',
                remote_addr=None,
                name='attachment_page',
                note='attachment note',
                attachment_filename='test.txt',
                attachment=File(evil),
            )

    def test_no_target_parameter_raises_http404(self):
        """Test that missing target parameter raises Http404."""
        factory = RequestFactory()
        request = factory.get('/wiki/_attachment/')
        request.user = self.user

        with self.assertRaises(Http404):
            get_attachment(request)

    def test_empty_target_parameter_raises_http404(self):
        """Test that empty target parameter raises Http404."""
        factory = RequestFactory()
        request = factory.get('/wiki/_attachment/?target=')
        request.user = self.user

        with self.assertRaises(Http404):
            get_attachment(request)

    def test_permission_denied_without_read_privilege(self):
        """Test that PermissionDenied is raised when user lacks read privilege."""
        # Create an ACL that denies read access
        Page.objects.create(
            'ACL',
            '#X-Behave: Access-Control-List\n'
            '{{{\n'
            '[*]\n'
            'user=none\n'
            '}}}',
            user=self.admin,
            note='init ACL',
        )

        factory = RequestFactory()
        request = factory.get('/wiki/_attachment/?target=attachment_page')
        request.user = self.user

        with self.assertRaises(PermissionDenied):
            get_attachment(request)

    def test_no_attachment_raises_http404(self):
        """Test that Http404 is raised when page has no attachment."""
        Page.objects.create( # page without attachment
            user=self.user,
            name='no_attachment',
            remote_addr='',
            text='text'
        )

        factory = RequestFactory()
        request = factory.get('/wiki/_attachment/?target=no_attachment')
        request.user = self.admin

        with self.assertRaises(Http404):
            get_attachment(request)

    def test_nonexistent_page_raises_http404(self):
        """Test that Http404 is raised when page does not exist."""
        factory = RequestFactory()
        request = factory.get('/wiki/_attachment/?target=nonexistent_page')
        request.user = self.admin

        with self.assertRaises(Http404):
            get_attachment(request)

    def test_successful_redirect_to_attachment(self):
        """Test successful redirect to attachment media URL."""
        factory = RequestFactory()
        request = factory.get('/wiki/_attachment/?target=attachment_page')
        request.user = self.admin

        response = get_attachment(request)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(f'//media.{settings.BASE_DOMAIN_NAME}/wiki/attachments/'))

    def test_target_normalized(self):
        """Test that target name is normalized before use."""
        factory = RequestFactory()
        request = factory.get('/wiki/_attachment/?target=attachment%20page')
        request.user = self.admin

        response = get_attachment(request)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(f'//media.{settings.BASE_DOMAIN_NAME}/wiki/attachments/'))

    def test_case_insensitive_target(self):
        """Test that target parameter is case-insensitive."""
        factory = RequestFactory()
        request = factory.get('/wiki/_attachment/?target=ATTACHMENT_PAGE')
        request.user = self.admin

        response = get_attachment(request)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(f'//media.{settings.BASE_DOMAIN_NAME}/wiki/attachments/'))

    def test_attachment_href_integration(self):
        """Test full integration with client."""
        url = href('wiki', '_attachment', target='attachment_page')
        response = self.client.get(url, follow=True)

        self.assertTrue(response.redirect_chain[0][0].startswith(f'//media.{settings.BASE_DOMAIN_NAME}/wiki/attachments/'))

    def test_special_characters_in_target(self):
        """Test handling of special characters in target parameter."""
        factory = RequestFactory()
        request = factory.get('/wiki/_attachment/?target=attachment page')
        request.user = self.admin

        response = get_attachment(request)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(f'//media.{settings.BASE_DOMAIN_NAME}/wiki/attachments/'))

    def test_anonymous_user_without_privilege(self):
        """Test that anonymous users are properly denied access."""
        # Create an ACL that denies anonymous access
        Page.objects.create(
            'ACL',
            '#X-Behave: Access-Control-List\n'
            '{{{\n'
            '[*]\n'
            'user=none\n'
            '}}}',
            user=self.admin,
            note='init ACL',
        )

        factory = RequestFactory()
        request = factory.get('/wiki/_attachment/?target=attachment_page')
        request.user = User.objects.get_anonymous_user()

        with self.assertRaises(PermissionDenied):
            get_attachment(request)


class TestTagRelatedViews(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()
        self.admin = User.objects.register_user('admin', 'admin', 'admin', False)
        self.client.defaults['HTTP_HOST'] = 'wiki.%s' % settings.BASE_DOMAIN_NAME
        self.client.login(username='admin', password='admin')

        self.p1 = Page.objects.create('testPage1', '\np1 \n # tag: test\n',
                                      user=self.admin, note='rev 0')
        self.p2 = Page.objects.create('testPage2', '\np2 \n # tag: another\n',
                                      user=self.admin, note='rev 0')

        self.p1.edit(user=self.admin,
                     text='''
p
# tag: test
''',
                     note="rev 1",
                     )
        self.p1.update_meta()

        self.p2.edit(user=self.admin,
                     text='''
another
# tag: another
''',
                     note="rev 1",
                     )
        self.p2.update_meta()

    def test_recentchanges__not_yet_generated(self):
        response = self.client.get('/wiki/recentchanges/')

        self.assertContains(response, 'Recent Changes are currently unavailable.')

    def test_missingpages__no_missing(self):
        response = self.client.get('/wiki/missingpages/')

        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(response.context['missingpages'], [])

    def test_randompages(self):
        response = self.client.get('/wiki/randompages/')

        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(response.context['randompages'], ['testPage1', 'testPage2', 'Wiki/Index'])

    def test_show_tag_list(self):
        response = self.client.get('/wiki/tags/')

        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(response.context['tag_list'],
                              [{'name': 'another', 'count': 1, 'size': 2},
                               {'name': 'test', 'count': 1, 'size': 2}])

    def test_show_tag_cloud(self):
        response = self.client.get('/wiki/tagcloud/')

        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(response.context['tag_list'], [{'name': 'another', 'count': 1, 'size': 2}, {'name': 'test', 'count': 1, 'size': 2}])

    def test_show_pages_by_tag__not_existing_tag(self):
        response = self.client.get('/wiki/tags/foo/')

        self.assertEqual(response.status_code, 404)

    def test_show_pages_by_tag(self):
        response = self.client.get('/wiki/tags/test/')

        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(response.context['page_list'], ['testPage1'])


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

        self.assertEqual(Page.objects.filter(name='newpage').count(), 1)

    def test_normalization_create(self):
        self.client.post(self.url, data={'name': 'new page', 'template': ''})

        self.assertEqual(Page.objects.get(name='new_page').name, 'new_page')

    def test_error_with_different_pagename_case(self):
        Page.objects.create(user=self.user, name='abc', remote_addr='', text='test')

        response = self.client.post(self.url, data={'name': 'Abc', 'template': ''})

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
        data = {'text': new_content, 'note': new_content, 'edit_time': datetime.now(timezone.utc),
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

    def test_name_with_different_case(self):
        url = href('wiki', self.page_name.upper())

        response = self.client.get(url, follow=True)
        self.assertRedirects(response, '/test_page/')

    def test_page_with_space_in_name(self):
        Page.objects.create('test_Page5', 'rev 0', user=self.user, note='rev 0')

        url = href('wiki', 'test Page5')
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)


class TestDoMetaExport(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()
        user = User.objects.register_user('user', 'user@example.test', 'user', False)

        self.page_name = 'test_page'
        page = Page.objects.create(user=user, name=self.page_name, remote_addr='', text=self.page_name)
        page.edit(user=user,
                       text='''
p
# tag: test, foo
''',
                       note="rev 1",
                       )
        page.update_meta()

        self.url = href('wiki', self.page_name, 'a', 'export', 'meta')

        self.client.login(username='user', password='user')
        self.client.defaults['HTTP_HOST'] = 'wiki.%s' % settings.BASE_DOMAIN_NAME

    def test_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, b'tag: foo')
        self.assertContains(response, b'tag: test')

    def test_missing_page(self):
        response = self.client.get(href('wiki', 'not_existing', 'a', 'export', 'meta'))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(b'', response.content)

    def test_name_with_different_case(self):
        url = href('wiki', self.page_name.upper(), 'a', 'export', 'meta')

        response = self.client.get(url, follow=True)
        self.assertRedirects(response, '/test_page/a/export/meta/')


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


class TestDoRevert(TestCase):
    client_class = InyokaClient

    def setUp(self):
        super().setUp()
        self.user = User.objects.register_user(
            'user', 'user@example.test', 'user', False
        )
        self.admin = User.objects.register_user(
            'admin', 'admin@example.test', 'admin', False
        )

        self.client.login(username='admin', password='admin')
        self.client.defaults['HTTP_HOST'] = 'wiki.%s' % settings.BASE_DOMAIN_NAME

        self.page = Page.objects.create(
            user=self.user, name='test_page', remote_addr='', text='revision 0'
        )

        self.page.edit(text='revision 1', user=self.user, note='Edit 1')
        self.page.edit(text='revision 2', user=self.user, note='Edit 2')

        revisions = self.page.revisions.all().order_by('id')
        self.rev_1 = revisions[0]
        self.rev_2 = revisions[1]
        self.rev_3 = revisions[2]

    def test_get_request_shows_form(self):
        """Test that GET request displays the revert confirmation form."""
        url = href('wiki', 'test_page', 'a', 'revert', self.rev_2.id)
        response = self.client.get(url, follow=True)

        self.assertRedirects(response, href('wiki', 'test_page', 'a', 'revision', self.rev_2.id))
        self.assertInHTML('<input type="submit" value="Restore">', response.content.decode())

    def test_post_cancel_revert(self):
        """Test that POST with cancel parameter aborts the revert."""
        url = href('wiki', 'test_page', 'a', 'revert', self.rev_2.id)
        response = self.client.post(
            url,
            data={'cancel': 'Cancel'},
            follow=True
        )

        self.assertContains(response, 'Revert aborted')

        # Verify page text hasn't changed
        page = Page.objects.get_by_name('test_page')
        self.assertEqual(page.rev.text.value, 'revision 2')

    def test_revert_non_existent_page(self):
        """Test that a non-existent page returns 404."""
        url = href('wiki', 'non_existent_page', 'a', 'revert', 1)
        response = self.client.get(url, follow=False)

        self.assertEqual(response.status_code, 404)

    def test_revert_non_existent_revision(self):
        """Test that a non-existent revision returns 404."""
        url = href('wiki', 'test_page', 'a', 'revert', 99999)
        response = self.client.get(url, follow=False)

        self.assertEqual(response.status_code, 404)

    def test_revert_without_permissions(self):
        """Test that anonymous user without 'manage' privilege sees login."""
        self.client.logout()

        Page.objects.create(
            'ACL',
            '#X-Behave: Access-Control-List\n'
            '{{{\n'
            '[*]\n'
            'user=none\n'
            '}}}',
            user=self.user,
            note='init ACL',
        )

        url = href('wiki', 'test_page', 'a', 'revert', self.rev_1.id)
        response = self.client.get(url, follow=True)

        self.assertEqual(len(response.redirect_chain), 1)
        self.assertTrue(response.redirect_chain[0][0].startswith(href('portal', 'login')))

    def test_post_revert_success(self):
        """Test successful revert to an older revision."""
        url = href('wiki', 'test_page', 'a', 'revert', self.rev_1.id)
        response = self.client.post(
            url,
            data={'note': 'Reverting to first revision'},
            follow=True
        )

        self.assertContains(response, 'was reverted successfully')

        # Verify page text has been reverted
        page = Page.objects.get_by_name('test_page')
        self.assertEqual(page.rev.text.value, 'revision 0')

        self.assertEqual(page.revisions.count(), 4)
        self.assertIn('Reverting to first revision', page.rev.note)

    def test_post_revert_latest_revision_error(self):
        """Test that reverting to the latest revision shows an error."""
        url = href('wiki', 'test_page', 'a', 'revert', self.rev_3.id)
        response = self.client.post(
            url,
            data={'note': 'Try to revert to latest'},
            follow=True
        )

        self.assertContains(response, 'Revision is the latest one, revert aborted')

        page = Page.objects.get_by_name('test_page')
        self.assertEqual(page.revisions.count(), 3)

    def test_revert_with_empty_note(self):
        """Test revert with empty note parameter."""
        url = href('wiki', 'test_page', 'a', 'revert', self.rev_1.id)
        response = self.client.post(
            url,
            data={'note': ''},
            follow=True
        )

        self.assertContains(response, 'was reverted successfully')

        # Verify new revision exists with empty note (but includes the default message)
        page = Page.objects.get_by_name('test_page')
        self.assertEqual(page.rev.text.value, 'revision 0')
        self.assertIn('restored]', page.rev.note)

    def test_revert_updates_page_last_rev(self):
        """Test that revert properly updates the page's last_rev."""
        original_last_rev_id = self.page.last_rev.id

        url = href('wiki', 'test_page', 'a', 'revert', self.rev_1.id)
        self.client.post(
            url,
            data={'note': 'Test revert'},
            follow=True
        )

        page_after = Page.objects.get_by_name('test_page')
        # last_rev should have changed
        self.assertNotEqual(page_after.last_rev.id, original_last_rev_id)

        # New revision should be the latest
        latest_rev = page_after.revisions.latest()
        self.assertEqual(page_after.last_rev.id, latest_rev.id)

    def test_revert_attachment(self):
        """Test that reverting a revision with attachment preserves the attachment."""

        with open(join(dirname(__file__), 'evil.png'), 'rb') as evil:
            attachment = Page.objects.create(
                user=self.user,
                text='text',
                remote_addr=None,
                name='attachment',
                note='attachment note',
                attachment_filename='foo.txt',
                attachment=File(evil),
            )
        attachment.edit(user=self.user)
        self.assertEqual(attachment.revisions.all().count(), 2)

        revisions = attachment.revisions.all().order_by('id')
        url = href('wiki', 'attachment', 'a', 'revert', revisions[0].id)
        response = self.client.post(
            url,
            data={'note': 'Revert'},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(attachment.revisions.all().count(), 3)

        page = Page.objects.get_by_name('attachment')
        self.assertIsNotNone(page.rev.attachment.filename)

    def test_post_revert_with_different_case_in_name__shows_form(self):
        """Test revert with different case in page name."""
        url = href('wiki', 'TEST_PAGE', 'a', 'revert', self.rev_1.id)
        response = self.client.get(url, follow=True)

        self.assertInHTML('<input type="submit" value="Restore">', response.content.decode())
        self.assertRedirects(response, href('wiki', f'test_page/a/revision/{self.rev_1.id}/'))


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

    def test_name_with_different_case(self):
        url = href('wiki', self.page.name.upper(), 'a', 'feed')

        response = self.client.get(url, follow=True)
        self.assertRedirects(response, '/test_page/a/feed/')

    def test_name_with_space(self):
        Page.objects.create('First_Steps', 'rev 0', user=self.user, note='rev 0')

        url = href('wiki', 'first steps', 'a', 'feed')
        response = self.client.get(url, follow=True)

        self.assertRedirects(response, '/First_Steps/a/feed/')

    def test_name_with_invalid_char(self):
        Page.objects.create('First_Steps', 'rev 0', user=self.user, note='rev 0')

        url = href('wiki', 'First #Steps', 'a', 'feed')
        response = self.client.get(url, follow=True)

        self.assertRedirects(response, '/First_Steps/a/feed/')

    def test_name_with_hierarchy(self):
        Page.objects.create('First_Steps/barz', 'rev 0', user=self.user, note='rev 0')

        url = href('wiki', 'First Steps/barz', 'a', 'feed')
        response = self.client.get(url, follow=True)

        self.assertRedirects(response, '/First_Steps/barz/a/feed/')

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
                       change_date=datetime.now(timezone.utc) + timedelta(minutes=11))
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
