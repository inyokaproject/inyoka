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


class TestDoRename(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()
        self.admin = User.objects.register_user('admin', 'admin@example.test', 'admin', False)
        self.user = User.objects.register_user('user', 'user@example.test', 'user', False)

        self.client.defaults['HTTP_HOST'] = 'wiki.%s' % settings.BASE_DOMAIN_NAME
        self.client.login(username='admin', password='admin')

        self.page = Page.objects.create(
            user=self.admin,
            name='test_page',
            remote_addr='',
            text='test content'
        )

    def test_get_request_shows_form(self):
        """Test that GET request displays the rename form with initial values."""
        url = href('wiki', 'test_page', 'a', 'rename')
        response = self.client.get(url, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertInHTML('<input type="text" name="new_name" size="30" value="test_page">', response.content.decode())

    def test_post_rename_success(self):
        """Test successful rename of a page."""
        url = href('wiki', 'test_page', 'a', 'rename')
        response = self.client.post(
            url,
            data={'new_name': 'renamed_page'},
            follow=True
        )

        self.assertRedirects(response, href('wiki', 'renamed_page'))
        self.assertContains(response, 'Renamed the page successfully')

        # Verify page was renamed
        self.page.refresh_from_db()
        self.assertEqual(self.page.name, 'renamed_page')

    def test_post_rename_with_empty_name(self):
        """Test rename with empty new_name shows error."""
        url = href('wiki', 'test_page', 'a', 'rename')
        response = self.client.post(
            url,
            data={'new_name': ''},
            follow=True
        )

        self.assertContains(response, 'No page name given')
        # Original page should still exist
        self.page.refresh_from_db()
        self.assertEqual(self.page.name, 'test_page')

    def test_post_rename_to_existing_page(self):
        """Test rename fails if target page already exists."""
        Page.objects.create( # another page
            user=self.admin,
            name='existing_page',
            remote_addr='',
            text='existing content'
        )

        url = href('wiki', 'test_page', 'a', 'rename')
        response = self.client.post(
            url,
            data={'new_name': 'existing_page'},
            follow=True
        )

        self.assertContains(response, 'A page with this name already exists')
        # Original page should still exist
        self.page.refresh_from_db()
        self.assertEqual(self.page.name, 'test_page')

    def test_post_rename_nonexistent_page(self):
        """Test rename on non-existent page returns 404."""
        url = href('wiki', 'nonexistent_page', 'a', 'rename')
        response = self.client.get(url, follow=False)

        self.assertEqual(response.status_code, 404)

    def test_post_rename_with_add_redirect(self):
        """Test rename creates redirect when add_redirect is checked."""
        url = href('wiki', 'test_page', 'a', 'rename')
        response = self.client.post(
            url,
            data={'new_name': 'renamed_page', 'add_redirect': 'on'},
            follow=True
        )

        self.assertContains(response, 'Renamed the page successfully')

        # Check new page exists
        renamed_page = Page.objects.get_by_name('renamed_page')
        self.assertEqual(renamed_page.name, 'renamed_page')

        # Check redirect page was created
        redirect_page = Page.objects.get_by_name('test_page')
        self.assertIn('X-Redirect: renamed_page', redirect_page.rev.text.value)

    def test_post_rename_normalizes_name(self):
        """Test that new page name is normalized."""
        url = href('wiki', 'test_page', 'a', 'rename')
        response = self.client.post(
            url,
            data={'new_name': 'new page name'},
            follow=True
        )

        self.assertContains(response, 'Renamed the page successfully')

        # Check normalized name is used
        self.page.refresh_from_db()
        self.assertEqual(self.page.name, 'new_page_name')

    def test_rename_without_manage_privilege(self):
        """Test that user without manage privilege cannot rename."""
        self.client.logout()
        self.client.login(username='user', password='user')

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

        url = href('wiki', 'test_page', 'a', 'rename')
        response = self.client.get(url, follow=True)

        self.assertEqual(response.status_code, 403)

    def test_rename_deleted_page(self):
        """Test rename on a deleted page returns 404."""
        self.page.edit(user=self.admin, deleted=True, note='deleted')

        url = href('wiki', 'test_page', 'a', 'rename')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_rename_with_attachment(self):
        """Test rename moves attachments correctly."""
        with open(join(dirname(__file__), 'evil.png'), 'rb') as evil:
            attachment = Page.objects.create(
                user=self.admin,
                text='attachment text',
                remote_addr=None,
                name='test_page/attachment1',
                note='attachment note',
                attachment_filename='foo.txt',
                attachment=File(evil),
            )

        url = href('wiki', 'test_page', 'a', 'rename')
        response = self.client.post(
            url,
            data={'new_name': 'renamed_page'},
            follow=True
        )

        self.assertContains(response, 'Renamed the page successfully')

        # Check attachment was moved
        attachment.refresh_from_db()
        self.assertEqual(attachment.name, 'renamed_page/attachment1')

    def test_rename_with_multiple_attachments(self):
        """Test rename moves multiple attachments correctly."""
        with open(join(dirname(__file__), 'evil.png'), 'rb') as evil:
            att1 = Page.objects.create(
                user=self.admin,
                text='att1',
                remote_addr=None,
                name='test_page/attachment1',
                note='att1',
                attachment_filename='file1.txt',
                attachment=File(evil),
            )

        with open(join(dirname(__file__), 'evil.png'), 'rb') as evil:
            att2 = Page.objects.create(
                user=self.admin,
                text='att2',
                remote_addr=None,
                name='test_page/attachment2',
                note='att2',
                attachment_filename='file2.txt',
                attachment=File(evil),
            )

        url = href('wiki', 'test_page', 'a', 'rename')
        response = self.client.post(
            url,
            data={'new_name': 'renamed_page'},
            follow=True
        )

        self.assertEqual(response.status_code, 200)

        # Check both attachments were moved
        att1.refresh_from_db()
        att2.refresh_from_db()
        self.assertEqual(att1.name, 'renamed_page/attachment1')
        self.assertEqual(att2.name, 'renamed_page/attachment2')

    def test_rename_with_conflicting_attachments_no_force(self):
        """Test rename fails when conflicting attachments exist (no force)."""
        # Create attachment on old page
        with open(join(dirname(__file__), 'evil.png'), 'rb') as evil:
            Page.objects.create(
                user=self.admin,
                text='old',
                remote_addr=None,
                name='test_page/shared_attachment',
                note='old att',
                attachment_filename='old.txt',
                attachment=File(evil),
            )

        # Create conflicting attachment on new page
        with open(join(dirname(__file__), 'evil.png'), 'rb') as evil:
            Page.objects.create(
                user=self.admin,
                text='new',
                remote_addr=None,
                name='renamed_page/shared_attachment',
                note='new att',
                attachment_filename='new.txt',
                attachment=File(evil),
            )

        url = href('wiki', 'test_page', 'a', 'rename')
        response = self.client.post(
            url,
            data={'new_name': 'renamed_page'},
            follow=True
        )

        self.assertContains(response, 'are already attached to the new page name')

        # Original page should still exist
        self.page.refresh_from_db()
        self.assertEqual(self.page.name, 'test_page')

    def test_rename_with_conflicting_attachments_force(self):
        """Test rename with force deletes conflicting attachments."""
        # Create attachment on old page
        with open(join(dirname(__file__), 'evil.png'), 'rb') as evil:
            att_old = Page.objects.create(
                user=self.admin,
                text='old',
                remote_addr=None,
                name='test_page/shared_attachment',
                note='old att',
                attachment_filename='old.txt',
                attachment=File(evil),
            )

        # Create conflicting attachment on new page
        with open(join(dirname(__file__), 'evil.png'), 'rb') as evil:
            att_new = Page.objects.create(
                user=self.admin,
                text='new',
                remote_addr=None,
                name='renamed_page/shared_attachment',
                note='new att',
                attachment_filename='new.txt',
                attachment=File(evil),
            )

        url = href('wiki', 'test_page', 'a', 'rename', 'force')
        response = self.client.post(
            url,
            data={'new_name': 'renamed_page'},
            follow=True
        )

        self.assertContains(response, 'Renamed the page successfully')

        # Old attachment should be moved
        att_old.refresh_from_db()
        self.assertEqual(att_old.name, 'renamed_page/shared_attachment')

        with self.assertRaises(Page.DoesNotExist):
            att_new.refresh_from_db()

    def test_rename_with_different_case_in_name(self):
        """Test rename works with different case in page name."""
        url = href('wiki', 'TEST_PAGE', 'a', 'rename')
        response = self.client.get(url, follow=True)

        self.assertRedirects(response, self.page.get_absolute_url())

    def test_rename_creates_revisions(self):
        """Test that rename creates new revisions for page and attachments."""
        original_rev_count = self.page.revisions.count()

        url = href('wiki', 'test_page', 'a', 'rename')
        self.client.post(
            url,
            data={'new_name': 'renamed_page'},
            follow=True
        )

        # Should have one more revision from the rename
        self.assertEqual(self.page.revisions.count(), original_rev_count + 1)

    def test_rename_preserves_content(self):
        """Test that rename preserves page content."""
        original_text = self.page.rev.text.value

        url = href('wiki', 'test_page', 'a', 'rename')
        self.client.post(
            url,
            data={'new_name': 'renamed_page'},
            follow=True
        )

        renamed_page = Page.objects.get_by_name('renamed_page')
        self.assertEqual(renamed_page.rev.text.value, original_text)

    def test_rename_get_returns_redirect_to_show(self):
        """Test that GET request without POST returns redirect to show."""
        url = href('wiki', 'test_page', 'a', 'rename')
        response = self.client.get(url, follow=False)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.page.get_absolute_url(), response.url)

    def test_rename_same_name_as_current(self):
        """Test rename to the same name shows error."""
        url = href('wiki', 'test_page', 'a', 'rename')
        response = self.client.post(
            url,
            data={'new_name': 'test_page'},
            follow=True
        )

        self.assertContains(response, 'A page with this name already exists.')

    def test_rename_hierarchy_preserved(self):
        """Test that rename preserves page hierarchy structure."""
        parent_page = Page.objects.create(
            user=self.admin,
            name='parent',
            remote_addr='',
            text='parent content'
        )

        child_page = Page.objects.create(
            user=self.admin,
            name='parent/child',
            remote_addr='',
            text='child content'
        )

        url = href('wiki', 'parent', 'a', 'rename')
        response = self.client.post(
            url,
            data={'new_name': 'new_parent'},
            follow=True
        )

        self.assertContains(response, 'Renamed the page successfully')

        # Parent should be renamed
        parent_page.refresh_from_db()
        self.assertEqual(parent_page.name, 'new_parent')

        # Child should still be under old parent (not automatically renamed)
        child_page.refresh_from_db()
        self.assertEqual(child_page.name, 'parent/child')

    def test_rename_attachment_with_text(self):
        """Test rename preserves attachment text/description."""
        with open(join(dirname(__file__), 'evil.png'), 'rb') as evil:
            Page.objects.create(
                user=self.admin,
                text='attachment description',
                remote_addr=None,
                name='test_page/mydoc',
                note='att note',
                attachment_filename='mydoc.pdf',
                attachment=File(evil),
            )

        url = href('wiki', 'test_page', 'a', 'rename')
        response = self.client.post(
            url,
            data={'new_name': 'renamed_page'},
            follow=True
        )

        self.assertContains(response, 'Renamed the page successfully')

        # Attachment text should be preserved
        renamed_att = Page.objects.get_by_name('renamed_page/mydoc')
        self.assertEqual(renamed_att.rev.text.value, 'attachment description')

    def test_rename_updates_last_rev(self):
        """Test that rename properly updates the page's last_rev."""
        original_last_rev_id = self.page.last_rev.id

        url = href('wiki', 'test_page', 'a', 'rename')
        self.client.post(
            url,
            data={'new_name': 'renamed_page'},
            follow=True
        )

        self.page.refresh_from_db()
        # last_rev should have changed
        self.assertNotEqual(self.page.last_rev.id, original_last_rev_id)

    def test_rename_anonymous_redirects_to_login(self):
        """Test that anonymous user is redirected to login."""
        self.client.logout()

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

        url = href('wiki', 'test_page', 'a', 'rename')
        response = self.client.get(url, follow=True)

        self.assertEqual(len(response.redirect_chain), 1)
        self.assertTrue(response.redirect_chain[0][0].startswith(href('portal', 'login')))


class TestDoDelete(TestCase):
    client_class = InyokaClient

    def setUp(self):
        super().setUp()
        self.user = User.objects.register_user('user', 'user@example.test', 'user',
                                               False)

        self.client.login(username='user', password='user')
        self.client.defaults['HTTP_HOST'] = 'wiki.%s' % settings.BASE_DOMAIN_NAME

        self.page = Page.objects.create(user=self.user, name='delete_test',
                                        remote_addr='', text='test content')
        self.url = self.page.get_absolute_url('delete')

    def test_get_shows_delete_form(self):
        """GET request should display the delete confirmation form."""
        response = self.client.get(self.url, follow=True)
        self.assertContains(response, 'Are you sure you want to delete this page?')

    def test_post_with_cancel(self):
        """POST request with 'cancel' in POST data should abort deletion."""
        response = self.client.post(self.url, data={'cancel': 'Cancel'}, follow=True)
        self.assertContains(response, 'Canceled.')

        # Verify page is not deleted
        page = Page.objects.get_by_name('delete_test')
        self.assertFalse(page.rev.deleted)

    def test_post_delete_page(self):
        """POST request without 'cancel' should delete the page."""
        response = self.client.post(self.url, data={'note': 'Test deletion'},
                                    follow=True)
        self.assertContains(response, 'Page deleted successfully.', status_code=404)

        # Verify page is marked as deleted
        page = Page.objects.get_by_name('delete_test')
        self.assertTrue(page.rev.deleted)

    def test_post_delete_page_without_note(self):
        """POST request without explicit note should use default note."""
        response = self.client.post(self.url, data={}, follow=True)
        self.assertContains(response, 'Page deleted successfully.', status_code=404)

        # Verify page is marked as deleted with default note
        page = Page.objects.get_by_name('delete_test')
        self.assertTrue(page.rev.deleted)
        self.assertEqual(page.rev.note, 'Page deleted.')

    def test_delete_nonexistent_page(self):
        """Trying to delete a non-existent page should return 404."""
        url = href('wiki', 'nonexistent_page', 'a', 'delete')
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 404)

    def test_delete_requires_privilege(self):
        """User without delete privilege should not be able to delete."""
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

        response = self.client.get(self.url, follow=True)
        self.assertEqual(response.status_code, 403)

    def test_delete_redirects_to_page(self):
        """After deletion, should redirect to the page URL."""
        response = self.client.post(self.url, data={'note': 'Test'})
        self.assertRedirects(response, self.page.get_absolute_url('show'), target_status_code=404)

    def test_delete_with_different_case_in_name(self):
        """Deleting a page with different case in URL should work."""
        url = href('wiki', 'DELETE_TEST', 'a', 'delete')
        response = self.client.post(url, data={'note': 'Test deletion'}, follow=True)

        self.assertContains(response, 'Are you sure you want to delete this page?')
        self.assertEqual(response.redirect_chain,
                         [('/delete_test/a/delete/', 302),
                          (href('wiki', 'delete_test'), 302)]
        )


class TestDoMvBaustelle(TestCase):
    client_class = InyokaClient

    def setUp(self):
        super().setUp()
        self.user = User.objects.register_user('user', 'user@example.test', 'user',
                                               False)
        self.admin = User.objects.register_user('admin', 'admin@example.test', 'admin',
                                                False)

        self.client.login(username='admin', password='admin')
        self.client.defaults['HTTP_HOST'] = 'wiki.%s' % settings.BASE_DOMAIN_NAME

    def _get_mv_baustelle_url(self, page_name):
        """Helper to get mv_baustelle URL."""
        return href('wiki', page_name, 'a', 'mv_baustelle')

    def _create_page(self, name, text='Test content', user=None):
        """Helper to create a wiki page."""
        if user is None:
            user = self.user
        return Page.objects.create(user=user, name=name, remote_addr='', text=text)

    def test_get_request_displays_form(self):
        """Test that GET request displays the form with correct initial values."""
        self._create_page('TestPage', 'Test content')
        url = self._get_mv_baustelle_url('TestPage')

        response = self.client.get(url)

        self.assertContains(response, 'Mark page “TestPage” as “under construction”')
        self.assertInHTML('<input type="text" name="new_name" value="Baustelle/TestPage" required id="id_new_name">', response.content.decode())

    def test_get_request_for_discontinued_page(self):
        """Test GET for pages in Baustelle/Verlassen (discontinued)."""
        self._create_page('Baustelle/Verlassen/TestPage', 'Test content')
        url = self._get_mv_baustelle_url('Baustelle/Verlassen/TestPage')

        response = self.client.get(url)

        # Should show Baustelle/TestPage (without Verlassen)
        self.assertInHTML(
            '<input type="text" name="new_name" value="Baustelle/TestPage" required id="id_new_name">',
            response.content.decode())

    def test_get_request_sets_user_initial(self):
        """Test that current user is set as initial form value."""
        self._create_page('TestPage', 'Test content')
        url = self._get_mv_baustelle_url('TestPage')

        response = self.client.get(url)

        # User should be pre-filled in the form
        self.assertInHTML(
            '<input type="text" name="user" value="admin" required id="id_user">',
            response.content.decode()
        )

    # Successful POST Tests (Normal Pages)

    def test_post_successful_move_without_completion_date(self):
        """Test successful move to Baustelle without completion date."""
        page = self._create_page('TestPage', 'Original content')
        url = self._get_mv_baustelle_url('TestPage')

        response = self.client.post(url, data={
            'new_name': 'Baustelle/TestPage',
            'user': self.admin.username,
            'completion_date': '',
        }, follow=True)

        self.assertContains(response, 'erfolgreich in die Baustelle verschoben')

        # Original page should be moved to Baustelle
        page.refresh_from_db()
        self.assertEqual(page.name, 'Baustelle/TestPage')

        # Copy should exist at original location
        copy_page = Page.objects.get_by_name('TestPage')
        self.assertIn('[[Vorlage(Kopie', copy_page.rev.text.value)

    def test_post_successful_move_with_completion_date(self):
        """Test successful move to Baustelle with completion date."""
        self._create_page('TestPage', 'Original content')
        url = self._get_mv_baustelle_url('TestPage')

        response = self.client.post(url, data={
            'new_name': 'Baustelle/TestPage',
            'user': self.admin.username,
            'completion_date': '2025-12-31',
        }, follow=True)

        self.assertContains(response, 'erfolgreich in die Baustelle verschoben')

        # Check that date is formatted correctly in template
        moved_page = Page.objects.get_by_name('Baustelle/TestPage')
        self.assertIn('31.12.2025', moved_page.rev.text.value)
        self.assertIn('Renamed from', moved_page.rev.note)

    def test_adds_template_on_move(self):
        """Test adds template when moving."""
        original_text = 'Original content'
        self._create_page('TestPage', original_text)
        url = self._get_mv_baustelle_url('TestPage')

        response = self.client.post(url, data={
            'new_name': 'Baustelle/TestPage',
            'user': self.admin.username,
            'completion_date': '',
        }, follow=True)

        self.assertContains(response, 'erfolgreich in die Baustelle verschoben')

        moved_page = Page.objects.get_by_name('Baustelle/TestPage')
        self.assertIn('[[Vorlage(Überarbeitung, TestPage, admin)]]', moved_page.rev.text.value)

    def test_post_preserves_user_in_template(self):
        """Test that user is preserved in Überarbeitung template."""
        self._create_page('TestPage', 'Original content')
        url = self._get_mv_baustelle_url('TestPage')

        self.client.post(url, data={
            'new_name': 'Baustelle/TestPage',
            'user': self.admin.username,
            'completion_date': '',
        }, follow=True)

        moved_page = Page.objects.get_by_name('Baustelle/TestPage')
        self.assertIn(self.admin.username, moved_page.rev.text.value)

    def test_copy_page_includes_original_page_name(self):
        """Test that copy page includes original page name in template."""
        self._create_page('TestPage', 'Original content')
        url = self._get_mv_baustelle_url('TestPage')

        self.client.post(url, data={
            'new_name': 'Baustelle/TestPage',
            'user': self.admin.username,
            'completion_date': '',
        }, follow=True)

        copy_page = Page.objects.get_by_name('TestPage')
        self.assertIn('[[Vorlage(Kopie, TestPage)', copy_page.rev.text.value)

    def test_copy_note_indicates_original_in_baustelle(self):
        """Test that copy note indicates original is in Baustelle."""
        self._create_page('TestPage', 'Original content')
        url = self._get_mv_baustelle_url('TestPage')

        self.client.post(url, data={
            'new_name': 'Baustelle/TestPage',
            'user': self.admin.username,
            'completion_date': '',
        }, follow=True)

        copy_page = Page.objects.get_by_name('TestPage')
        self.assertIn('Original in der Baustelle', copy_page.rev.note)

    # Discontinued Page Tests

    def test_post_move_discontinued_page_no_copy_created(self):
        """Test that no copy is created when moving discontinued pages."""
        page = self._create_page('Baustelle/Verlassen/TestPage', 'Original content')
        url = self._get_mv_baustelle_url('Baustelle/Verlassen/TestPage')

        response = self.client.post(url, data={
            'new_name': 'Baustelle/TestPage',
            'user': self.admin.username,
            'completion_date': '',
        }, follow=True)

        self.assertContains(response, 'erfolgreich in die Baustelle verschoben')

        page.refresh_from_db()
        self.assertEqual(page.name, 'Baustelle/TestPage')

        # No copy should exist at old location for discontinued pages
        with self.assertRaises(Page.DoesNotExist):
            Page.objects.get_by_name('Baustelle/Verlassen/TestPage')

    def test_post_removes_verlassen_template(self):
        """Test removal of Verlassen template from discontinued pages."""
        original_text = '[[Vorlage(Verlassen)]]\nOriginal content'
        self._create_page('Baustelle/Verlassen/TestPage', original_text)
        url = self._get_mv_baustelle_url('Baustelle/Verlassen/TestPage')

        self.client.post(url, data={
            'new_name': 'Baustelle/TestPage',
            'user': self.admin.username,
            'completion_date': '',
        }, follow=True)

        moved_page = Page.objects.get_by_name('Baustelle/TestPage')
        # Verlassen template should be removed
        self.assertNotIn('[[Vorlage(Verlassen', moved_page.rev.text.value)

    def test_verlassen_page__multiple_template_lines(self):
        """Test handling of multiple template lines."""
        original_text = '[[Vorlage(Verlassen)]]\n[[Vorlage(Something)]]\nOriginal content'
        self._create_page('Baustelle/Verlassen/TestPage', original_text)
        url = self._get_mv_baustelle_url('Baustelle/Verlassen/TestPage')

        self.client.post(url, data={
            'new_name': 'Baustelle/TestPage',
            'user': self.admin.username,
            'completion_date': '',
        }, follow=True)

        moved_page = Page.objects.get_by_name('Baustelle/TestPage')
        # Only Verlassen template should be removed
        self.assertIn('[[Vorlage(Something)', moved_page.rev.text.value)
        self.assertNotIn('[[Vorlage(Verlassen', moved_page.rev.text.value)

    def test_post_page_already_exists_error(self):
        """Test error when target page already exists."""
        self._create_page('TestPage', 'Original content')
        self._create_page('Baustelle/TestPage', 'Already exists')
        url = self._get_mv_baustelle_url('TestPage')

        response = self.client.post(url, data={
            'new_name': 'Baustelle/TestPage',
            'user': self.admin.username,
            'completion_date': '',
        }, follow=True)

        self.assertContains(response, 'bereits eine Seite')

    def test_post_form_invalid_data(self):
        """Test form validation with invalid data."""
        page = self._create_page('TestPage', 'Test content')
        url = self._get_mv_baustelle_url('TestPage')

        # Missing required field 'user'
        response = self.client.post(url, data={
            'new_name': 'Baustelle/TestPage',
            'completion_date': '',
        }, follow=False)

        self.assertContains(response, 'Mark page “TestPage” as “under construction”')

        # page should not be renamed
        page.refresh_from_db()
        self.assertEqual(page.name, 'TestPage')

    def test_page_does_not_exist_404(self):
        """Test 404 for non-existent pages."""
        url = self._get_mv_baustelle_url('NonExistentPage')

        response = self.client.get(url, follow=False)

        self.assertEqual(response.status_code, 404)

    def test_page_deleted_error(self):
        """Test error for deleted pages."""
        page = self._create_page('TestPage', 'Test content')
        page.edit(user=self.user, deleted=True, note='deleted')
        url = self._get_mv_baustelle_url('TestPage')

        response = self.client.get(url, follow=False)

        self.assertEqual(response.status_code, 404)

    def test_anonymous_redirect_to_login(self):
        self.client.logout()
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

        self._create_page('TestPage', 'Test content')
        url = self._get_mv_baustelle_url('TestPage')

        response = self.client.get(url, follow=True)

        # Should redirect to login
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertTrue(
            response.redirect_chain[0][0].startswith(href('portal', 'login')))

    def test_rename_failure_returns_error_message(self):
        """Test error handling when rename fails."""
        self._create_page('TestPage', 'Original content')
        url = self._get_mv_baustelle_url('TestPage')

        # Mock _rename to return False (failure)
        with patch('inyoka.wiki.actions._rename', return_value=False):
            response = self.client.post(url, data={
                'new_name': 'Baustelle/TestPage',
                'user': self.admin.username,
                'completion_date': '',
            }, follow=True)

        self.assertContains(response, 'Fehler')

    def test_hierarchical_page_names(self):
        """Test with hierarchical page names."""
        page = self._create_page('Category/SubCategory/TestPage', 'Content')
        url = self._get_mv_baustelle_url('Category/SubCategory/TestPage')

        response = self.client.post(url, data={
            'new_name': 'Baustelle/Category/SubCategory/TestPage',
            'user': self.admin.username,
            'completion_date': '',
        }, follow=True)

        self.assertContains(response, 'erfolgreich in die Baustelle verschoben')

        page.refresh_from_db()
        self.assertEqual(page.name, 'Baustelle/Category/SubCategory/TestPage')


class TestDoMvDiscontinued(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()
        self.user = User.objects.register_user('user', 'user@example.test', 'user', False)
        self.admin = User.objects.register_user('admin', 'admin@example.test', 'admin', False)

        self.client.login(username='admin', password='admin')
        self.client.defaults['HTTP_HOST'] = 'wiki.%s' % settings.BASE_DOMAIN_NAME

        self.page = Page.objects.create(
            user=self.user,
            name='Baustelle/test_page',
            remote_addr='',
            text='[[Vorlage(Baustelle)]]\nTest content'
        )

    def test_get_request_shows_flash_form(self):
        """Test that GET request displays the flash message form."""
        url = self.page.get_absolute_url('mv_discontinued')
        response = self.client.get(url, follow=True)

        # GET request should show flash message and redirect to show
        self.assertContains(response, 'Are you sure you want to mark the page as “discontinued”')
        self.assertRedirects(response, href('wiki', 'Baustelle/test_page'))

    def test_post_cancel_mv_discontinued(self):
        """Test that POST with cancel parameter aborts the move."""
        url = self.page.get_absolute_url('mv_discontinued')
        response = self.client.post(
            url,
            data={'cancel': 'Cancel'},
            follow=True
        )

        self.assertContains(response, 'Verschieben wurde abgebrochen.')

        # Verify page name hasn't changed
        self.page.refresh_from_db()
        self.assertEqual(self.page.name, 'Baustelle/test_page')

    def test_post_mv_discontinued_success(self):
        """Test successful move from Baustelle to Baustelle/Verlassen."""
        url = self.page.get_absolute_url('mv_discontinued')
        response = self.client.post(
            url,
            data={},
            follow=True
        )

        self.assertContains(response, 'Seite wurde erfolgreich verschoben.')

        # Verify page has been renamed
        self.page.refresh_from_db()
        self.assertEqual(self.page.name, 'Baustelle/Verlassen/test_page')

        # Verify the Verlassen box added
        page = Page.objects.get_by_name('Baustelle/Verlassen/test_page')
        self.assertIn('[[Vorlage(Verlassen)]]', page.rev.text.value)
        self.assertNotIn('[[Vorlage(Baustelle)]]', page.rev.text.value)
        self.assertIn('Test content', page.rev.text.value)

    def test_post_mv_discontinued_page_already_exists(self):
        """Test that error message shown when target page already exists."""
        Page.objects.create(
            user=self.user,
            name='Baustelle/Verlassen/test_page',
            remote_addr='',
            text='Existing page'
        )

        url = self.page.get_absolute_url('mv_discontinued')
        response = self.client.post(url, data={}, follow=True)

        # Should show error and redirect back
        self.assertContains(response, 'existiert bereits')
        self.assertRedirects(response, href('wiki', 'Baustelle/test_page'))

        # Page should not have been renamed
        self.assertTrue(Page.objects.filter(name='Baustelle/test_page').exists())

    def test_post_mv_discontinued_rename_fails(self):
        """Test handling when _rename function fails."""
        url = self.page.get_absolute_url('mv_discontinued')

        # Mock _rename to return False
        with patch('inyoka.wiki.actions._rename', return_value=False):
            response = self.client.post(url, data={}, follow=True)

        self.assertContains(response, 'Beim Verschieben ist ein Fehler aufgetreten.')
        self.assertRedirects(response, href('wiki', 'Baustelle/test_page'))

    def test_post_mv_discontinued_non_existent_page(self):
        """Test that non-existent page returns 404."""
        url = href('wiki', 'Baustelle/non_existent', 'a', 'mv_discontinued')
        response = self.client.get(url, follow=False)

        self.assertEqual(response.status_code, 404)

    def test_post_mv_discontinued_deleted_page(self):
        """Test that deleted page cannot be moved."""
        deleted_page = Page.objects.create(
            user=self.user,
            name='Baustelle/deleted_page',
            remote_addr='',
            text='Content'
        )
        deleted_page.edit(user=self.user, deleted=True, note='deleted')

        url = deleted_page.get_absolute_url('mv_discontinued')
        response = self.client.get(url, follow=False)

        self.assertEqual(response.status_code, 404)

    def test_post_mv_discontinued_preserves_content(self):
        """Test that page content is preserved during move."""
        original_content = 'Important content to preserve'
        page = Page.objects.create(
            user=self.user,
            name='Baustelle/preserve_test',
            remote_addr='',
            text=original_content
        )

        url = page.get_absolute_url('mv_discontinued')
        self.client.post(url, data={}, follow=True)

        moved_page = Page.objects.get_by_name('Baustelle/Verlassen/preserve_test')
        self.assertIn(original_content, moved_page.rev.text.value)

    def test_post_mv_discontinued_already_in_verlassen(self):
        """Test moving a page already in Baustelle/Verlassen."""
        # Create a page already in Verlassen
        page = Page.objects.create(
            user=self.user,
            name='Baustelle/Verlassen/already_discontinued',
            remote_addr='',
            text='[[Vorlage(Verlassen)]]\nContent'
        )

        url = page.get_absolute_url('mv_discontinued')
        self.client.post(url, data={}, follow=True)

        # Name transformation: Baustelle/Verlassen/X -> Baustelle/Verlassen/Verlassen/X
        expected_name = 'Baustelle/Verlassen/Verlassen/already_discontinued'
        moved_page = Page.objects.get_by_name(expected_name)
        self.assertEqual(moved_page.name, expected_name)

    def test_post_mv_discontinued_updates_revision_count(self):
        """Test that a new revision is created during the move."""
        initial_rev_count = self.page.revisions.count()

        url = self.page.get_absolute_url('mv_discontinued')
        self.client.post(url, data={}, follow=True)

        moved_page = Page.objects.get_by_name('Baustelle/Verlassen/test_page')
        # Should have one more revision (from the rename operation)
        self.assertEqual(moved_page.revisions.count(), initial_rev_count+1)

    def test_post_mv_discontinued_requires_manage_privilege(self):
        """Test that manage privilege is required."""
        self.client.logout()
        self.client.login(username='user', password='user')

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

        url = self.page.get_absolute_url('mv_discontinued')
        response = self.client.get(url, follow=True)

        # Should get permission error
        self.assertEqual(response.status_code, 403)

    def test_post_mv_discontinued_normalizes_pagename(self):
        """Test that page names are normalized."""
        Page.objects.create(
            user=self.user,
            name='Baustelle/spaced_page',
            remote_addr='',
            text='Content'
        )

        url = href('wiki', 'Baustelle/spaced page', 'a', 'mv_discontinued')
        self.client.post(url, data={}, follow=True)

        # Page should exist with normalized name
        self.assertTrue(
            Page.objects.filter(name='Baustelle/Verlassen/spaced_page').exists()
        )

    def test_post_mv_discontinued_multiline_text_handling(self):
        """Test handling of multi-line page text with template."""
        multiline_text = '[[Vorlage(Baustelle, info, user)]]\nLine 1\nLine 2\nLine 3'
        page = Page.objects.create(
            user=self.user,
            name='Baustelle/multiline_test',
            remote_addr='',
            text=multiline_text
        )

        url = page.get_absolute_url('mv_discontinued')
        self.client.post(url, data={}, follow=True)

        moved_page = Page.objects.get_by_name('Baustelle/Verlassen/multiline_test')
        text = moved_page.rev.text.value

        self.assertEqual(text,
                         '[[Vorlage(Verlassen)]]\nLine 1\nLine 2\nLine 3'
                         )


class TestDoMvBack(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()
        self.admin = User.objects.register_user(
            'admin', 'admin@example.test', 'admin', False
        )
        self.user = User.objects.register_user(
            'user', 'user@example.test', 'user', False
        )

        self.client.login(username='admin', password='admin')
        self.client.defaults['HTTP_HOST'] = 'wiki.%s' % settings.BASE_DOMAIN_NAME

    def test_get_request_shows_form(self):
        """Test that GET request displays the confirmation form."""
        page = Page.objects.create(
            user=self.user, name='Baustelle/test_page', remote_addr='',
            text='test content'
        )

        url = page.get_absolute_url('mv_back')
        response = self.client.get(url, follow=True)

        self.assertContains(response, 'Are you sure you want to move the page into the wiki?')

    def test_post_cancel_aborts_mv_back(self):
        """Test that POST with cancel parameter aborts the move."""
        page = Page.objects.create(
            user=self.user, name='Baustelle/test_page', remote_addr='',
            text='test content'
        )

        url = page.get_absolute_url('mv_back')
        response = self.client.post(
            url,
            data={'cancel': 'Cancel'},
            follow=True
        )

        self.assertContains(response, 'Wiederherstellen wurde abgebrochen.')

        # Verify page name hasn't changed
        page.refresh_from_db()
        self.assertEqual(page.name, 'Baustelle/test_page')

    def test_mv_back_from_baustelle_no_copy(self):
        """Test moving page back from Baustelle when no copy exists."""
        page = Page.objects.create(
            user=self.user,
            name='Baustelle/test_page',
            remote_addr='',
            text='[[Vorlage(Baustelle)]]\ntest content'
        )

        url = page.get_absolute_url('mv_back')
        response = self.client.post(
            url,
            data={},
            follow=True
        )

        self.assertContains(response, 'Seite erfolgreich ins Wiki verschoben')

        # Verify page was renamed
        page.refresh_from_db()
        self.assertEqual(page.name, 'test_page')

        # Verify box was removed from text
        page = Page.objects.get_by_name(page.name)
        self.assertNotIn('[[Vorlage(Baustelle', page.rev.text.value)
        self.assertEqual(page.rev.text.value, 'test content')

    def test_mv_back_with_ueberarbeitung_box(self):
        """Test moving page back when it has Überarbeitung box."""
        page = Page.objects.create(
            user=self.user,
            name='Baustelle/test_page',
            remote_addr='',
            text='[[Vorlage(Überarbeitung, 1.1.2023, admin)]]\ntest content'
        )

        url = page.get_absolute_url('mv_back')
        response = self.client.post(url, data={}, follow=True)

        self.assertContains(response, 'Seite erfolgreich ins Wiki verschoben')

        page.refresh_from_db()
        self.assertEqual(page.name, 'test_page')
        page = Page.objects.get_by_name(page.name)
        self.assertEqual(page.rev.text.value, 'test content')

    def test_mv_back_with_copy_exists(self):
        """Test moving page back when a copy exists at destination."""
        # Create page in Baustelle
        baustelle_page = Page.objects.create(
            user=self.user,
            name='Baustelle/test_page',
            remote_addr='',
            text='[[Vorlage(Baustelle)]]\noriginal content'
        )

        # Create copy at destination
        copy = Page.objects.create(
            user=self.user,
            name='test_page',
            remote_addr='',
            text='[[Vorlage(Kopie, Baustelle/test_page)]]\ncopy content'
        )

        url = baustelle_page.get_absolute_url('mv_back')
        response = self.client.post(url, data={}, follow=True)

        self.assertContains(response, 'Seite erfolgreich ins Wiki verschoben')

        # Verify original page was renamed
        baustelle_page.refresh_from_db()
        self.assertEqual(baustelle_page.name, 'test_page')

        # Verify copy was moved to Trash
        copy.refresh_from_db()
        self.assertEqual(copy.name, 'Trash/test_page-1')

    def test_mv_back_with_copy_multiple_trash_conflicts(self):
        """Test moving page back when Trash slots are occupied."""
        # Create page in Baustelle
        baustelle_page = Page.objects.create(
            user=self.user,
            name='Baustelle/article',
            remote_addr='',
            text='[[Vorlage(Baustelle)]]\noriginal'
        )

        # Create copy at destination
        copy = Page.objects.create(
            user=self.user,
            name='article',
            remote_addr='',
            text='[[Vorlage(Kopie, Baustelle/article)]]\ncopy'
        )

        # Create some conflicting Trash entries
        for i in range(1, 3):
            Page.objects.create(
                user=self.user,
                name=f'Trash/article-{i}',
                remote_addr='',
                text='conflict'
            )

        url = baustelle_page.get_absolute_url('mv_back')
        response = self.client.post(url, data={}, follow=True)

        self.assertContains(response, 'Seite erfolgreich ins Wiki verschoben')

        # Verify copy was moved to first available Trash slot
        copy.refresh_from_db()
        self.assertEqual(copy.name, 'Trash/article-3')

    def test_mv_back_non_baustelle_page_no_prefix(self):
        """Test moving back a page that doesn't start with Baustelle/."""
        page = Page.objects.create(
            user=self.user,
            name='test_page',
            remote_addr='',
            text='test content'
        )

        url = page.get_absolute_url('mv_back')
        response = self.client.post(url, data={}, follow=True)

        self.assertContains(response, 'Seite erfolgreich ins Wiki verschoben')

        # Verify page name remains unchanged (new_name = name in this case)
        page.refresh_from_db()
        self.assertEqual(page.name, 'test_page')

    def test_mv_back_non_existent_page_404(self):
        """Test that moving back a non-existent page returns 404."""
        url = href('wiki', 'Baustelle/non_existent', 'a', 'mv_back')
        response = self.client.get(url, follow=False)

        self.assertEqual(response.status_code, 404)

    def test_mv_back_without_permissions_redirects_to_login(self):
        """Test that user without manage privilege is redirected to login."""
        self.client.logout()

        # Create ACL restricting access
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

        page = Page.objects.create(
            user=self.user,
            name='Baustelle/test_page',
            remote_addr='',
            text='test content'
        )

        url = page.get_absolute_url('mv_back')
        response = self.client.get(url, follow=True)

        self.assertEqual(len(response.redirect_chain), 1)
        self.assertTrue(
            response.redirect_chain[0][0].startswith(href('portal', 'login')))

    def test_mv_back_with_different_case_in_name(self):
        """Test mv_back with different case in page name."""
        Page.objects.create(
            user=self.user,
            name='Baustelle/Test_Page',
            remote_addr='',
            text='test content'
        )

        url = href('wiki', 'BAUSTELLE/TEST_PAGE', 'a', 'mv_back')
        response = self.client.post(url, data={}, follow=True)

        self.assertContains(response, 'Are you sure you want to move the page into the wiki?')

    def test_mv_back_with_hierarchy_in_page_name(self):
        """Test mv_back with hierarchical page names."""
        page = Page.objects.create(
            user=self.user,
            name='Baustelle/Category/test_page',
            remote_addr='',
            text='[[Vorlage(Baustelle)]]\ntest content'
        )

        url = page.get_absolute_url('mv_back')
        response = self.client.post(url, data={}, follow=True)

        self.assertContains(response, 'Seite erfolgreich ins Wiki verschoben')

        page.refresh_from_db()
        self.assertEqual(page.name, 'Category/test_page')

    def test_mv_back_success_message_with_acl_link(self):
        """Test that success message contains link to ACL page."""
        page = Page.objects.create(
            user=self.user,
            name='Baustelle/test_page',
            remote_addr='',
            text='test content'
        )

        url = page.get_absolute_url('mv_back')
        response = self.client.post(url, data={}, follow=True)

        self.assertContains(response, 'Wiki/ACL/All-in-One')

    def test_mv_back_rename_failure_error_message(self):
        """Test error message when rename operation fails."""
        # Create a page that will cause _rename to fail
        page = Page.objects.create(
            user=self.user,
            name='Baustelle/test_page',
            remote_addr='',
            text='test content'
        )

        Page.objects.create(
            user=self.user,
            name='test_page',
            remote_addr='',
            text='[[Vorlage(Kopie, some_other_page)]]\ncopy'
        )

        # We need to fill all Trash slots (1-99)
        for i in range(1, 100):
            Page.objects.create(
                user=self.user,
                name=f'Trash/test_page-{i}',
                remote_addr='',
                text='trash'
            )

        url = page.get_absolute_url('mv_back')
        response = self.client.post(url, data={}, follow=True)

        self.assertContains(response, 'Kopie konnte nicht nach Trash verschoben werden')

        # Verify page was not renamed
        page.refresh_from_db()
        self.assertEqual(page.name, 'Baustelle/test_page')

    def test_mv_back_updates_page_last_rev(self):
        """Test that mv_back properly updates the page's last_rev."""
        page = Page.objects.create(
            user=self.user,
            name='Baustelle/test_page',
            remote_addr='',
            text='[[Vorlage(Baustelle)]]\ntest content'
        )
        original_rev_count = page.revisions.count()

        url = page.get_absolute_url('mv_back')
        self.client.post(url, data={}, follow=True)

        # mv_back should create a new revision via _rename
        self.assertEqual(page.revisions.count(), original_rev_count + 1)

    def test_mv_back_rename_fails(self):
        """Test handling when _rename function fails."""
        page = Page.objects.create(
            user=self.user,
            name='Baustelle/test_page',
            remote_addr='',
            text='[[Vorlage(Baustelle)]]\ntest content'
        )
        url = page.get_absolute_url('mv_back')

        # Mock _rename to return False
        with patch('inyoka.wiki.actions._rename', return_value=False):
            response = self.client.post(url, data={}, follow=True)

        self.assertContains(response, 'Beim Verschieben ist ein Fehler aufgetreten.')
        self.assertRedirects(response, href('wiki', 'Baustelle/test_page'))

    def test_mv_back__different_case_in_trash(self):
        page = Page.objects.create(
            user=self.user,
            name='Baustelle/test_page',
            remote_addr='',
            text='[[Vorlage(Baustelle)]]\ntest content'
        )

        copy = Page.objects.create(
            user=self.user,
            name='test_page',
            remote_addr='',
            text='[[Vorlage(Kopie, some_other_page)]]\ncopy'
        )

        Page.objects.create(
            user=self.user,
            name='Trash/Test_page-1',
            remote_addr='',
            text='trash'
        )

        url = page.get_absolute_url('mv_back')
        response = self.client.post(url, data={}, follow=True)

        self.assertContains(response, 'Seite erfolgreich ins Wiki verschoben')
        self.assertRedirects(response, href('wiki', 'test_page'))

        page.refresh_from_db()
        self.assertEqual(page.name, 'test_page')

        copy.refresh_from_db()
        self.assertEqual(copy.name, 'Trash/test_page-2')


class TestDoBacklinks(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()
        self.user = User.objects.register_user(
            'user', 'user@example.test', 'user', False
        )
        self.client.login(username='user', password='user')
        self.client.defaults['HTTP_HOST'] = 'wiki.%s' % settings.BASE_DOMAIN_NAME

        self.target_page_name = 'target_page'
        self.target_page = Page.objects.create(
            user=self.user,
            name=self.target_page_name,
            remote_addr='',
            text='This is the target page'
        )

    def test_backlinks_basic_get(self):
        """Test basic GET request to backlinks page."""
        url = self.target_page.get_absolute_url('backlinks')
        response = self.client.get(url)
        self.assertContains(response, self.target_page_name)

    def test_backlinks_deny_robots_flag(self):
        """Test that the deny_robots flag is set in the response."""
        url = self.target_page.get_absolute_url('backlinks')
        response = self.client.get(url)

        self.assertContains(response, '<meta name="robots" content="noindex, nofollow">')

    def test_backlinks_with_case_insensitive_page_name(self):
        url = href('wiki', self.target_page_name.upper(), 'a', 'backlinks')
        response = self.client.get(url, follow=True)

        self.assertRedirects(response, f'/{self.target_page_name}/a/backlinks/')

    def test_backlinks_with_page_having_links_to_it(self):
        """Test backlinks when other pages link to this page."""
        linking_page_name = 'linking_page'
        linking_page = Page.objects.create(
            user=self.user,
            name=linking_page_name,
            remote_addr='',
            text=f'This page links to [:{self.target_page_name}:]',
        )
        linking_page.update_meta()

        url = self.target_page.get_absolute_url('backlinks')
        response = self.client.get(url)
        self.assertContains(response, self.target_page_name)
        self.assertContains(response, linking_page_name)

    def test_backlinks_with_deleted_page(self):
        """Test that backlinks works for deleted pages (should not fail)."""
        self.target_page.edit(user=self.user, deleted=True, note='deleted')

        url = self.target_page.get_absolute_url('backlinks')
        response = self.client.get(url)

        self.assertContains(response, 'This article is an orphan and not referenced by any site.')

    def test_backlinks_with_multiple_links(self):
        """Test backlinks when multiple pages link to the target."""
        for i in range(3):
            linking_page_name = f'linking_page_{i}'
            linking_text = f'Page {i} links to [:{self.target_page_name}:]'
            linking_page = Page.objects.create(
                user=self.user,
                name=linking_page_name,
                remote_addr='',
                text=linking_text
            )
            linking_page.update_meta()

        url = self.target_page.get_absolute_url('backlinks')
        response = self.client.get(url)

        self.assertContains(response, self.target_page_name)
        for i in range(3):
            self.assertContains(response, f'linking_page_{i}')

    def test_backlinks_with_space_in_page_name(self):
        """Test backlinks with spaces converted to underscores in page name."""
        Page.objects.create(
            user=self.user,
            name='test_page_with_spaces',
            remote_addr='',
            text='Page with spaces in name'
        )

        url = href('wiki', 'test page with spaces', 'a', 'backlinks')
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_backlinks_with_different_case_redirects(self):
        """Test that case-sensitive redirect works correctly."""
        url = href('wiki', 'TARGET_PAGE', 'a', 'backlinks')
        response = self.client.get(url, follow=True)

        self.assertRedirects(response, f'/{self.target_page_name}/a/backlinks/')


class TestDoExport(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()
        self.user = User.objects.register_user(
            'user', 'user@example.test', 'user', False
        )

        self.page_name = 'test_page'
        self.page = Page.objects.create(
            user=self.user, name=self.page_name, remote_addr='', text='initial content'
        )

        self.client.login(username='user', password='user')
        self.client.defaults['HTTP_HOST'] = 'wiki.%s' % settings.BASE_DOMAIN_NAME

    def test_export_raw_latest_revision(self):
        """Test exporting raw format of the latest revision."""
        url = self.page.get_absolute_url('export', format='raw')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/plain; charset=utf-8')
        self.assertEqual(response['X-Robots-Tag'], 'noindex')
        self.assertIn(b'initial content', response.content)

    def test_export_html_latest_revision(self):
        """Test exporting HTML format of the latest revision."""
        url = self.page.get_absolute_url('export', format='html')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')
        self.assertEqual(response['X-Robots-Tag'], 'noindex')
        self.assertIn(b'initial content', response.content)

    def test_export_raw_specific_revision_numeric_id(self):
        """Test exporting raw format of a specific numeric revision."""
        # Create a new revision
        self.page.edit(text='updated content', user=self.user, note='Update')

        # Get the first revision ID
        first_rev_id = self.page.revisions.all().order_by('id').first().id

        url = self.page.get_absolute_url('export', format='raw', revision=first_rev_id)
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/plain; charset=utf-8')
        self.assertIn(b'initial content', response.content)

    def test_export_html_specific_revision_numeric_id(self):
        """Test exporting HTML format of a specific numeric revision."""
        # Create a new revision
        self.page.edit(text='updated content', user=self.user, note='Update')

        # Get the first revision ID
        first_rev_id = self.page.revisions.all().order_by('id').first().id

        url = self.page.get_absolute_url('export', format='html', revision=first_rev_id)
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')

    def test_export_raw_invalid_revision_string(self):
        """Test exporting with invalid (non-numeric) revision parameter falls back to latest."""
        url = self.page.get_absolute_url('export', format='raw', revision='invalid')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/plain; charset=utf-8')
        self.assertIn(b'initial content', response.content)

    def test_export_html_invalid_revision_string(self):
        """Test exporting HTML with invalid (non-numeric) revision parameter falls back to latest."""
        url = self.page.get_absolute_url('export', format='html',
                                         revision='not_a_number')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')

    def test_export_nonexistent_page(self):
        """Test exporting a non-existent page returns 404."""
        url = href('wiki', 'nonexistent_page', 'a', 'export', 'raw')
        response = self.client.get(url, follow=False)

        self.assertEqual(response.status_code, 404)

    def test_export_nonexistent_revision_numeric(self):
        """Test exporting a non-existent numeric revision returns 404."""
        url = self.page.get_absolute_url('export', format='raw', revision=99999)
        response = self.client.get(url, follow=False)

        self.assertEqual(response.status_code, 404)

    def test_export_deleted_page_raw(self):
        """Test exporting a deleted page returns 404."""
        self.page.edit(user=self.user, deleted=True, note='deleted')

        url = self.page.get_absolute_url('export', format='raw')
        response = self.client.get(url, follow=False)

        self.assertEqual(response.status_code, 404)

    def test_export_deleted_page_html(self):
        """Test exporting a deleted page in HTML format returns 404."""
        self.page.edit(user=self.user, deleted=True, note='deleted')

        url = self.page.get_absolute_url('export', format='html')
        response = self.client.get(url, follow=False)

        self.assertEqual(response.status_code, 404)

    def test_export_raw_default_format(self):
        """Test that raw is the default format when not specified."""
        url = href('wiki', self.page_name, 'a', 'export')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/plain; charset=utf-8')
        self.assertIn(b'initial content', response.content)

    def test_export_robots_tag_noindex(self):
        """Test that X-Robots-Tag header is set to noindex."""
        url = self.page.get_absolute_url('export', format='raw')
        response = self.client.get(url)

        self.assertEqual(response['X-Robots-Tag'], 'noindex')

    def test_export_robots_tag_noindex_html(self):
        """Test that X-Robots-Tag header is set to noindex for HTML exports."""
        url = self.page.get_absolute_url('export', format='html')
        response = self.client.get(url)

        self.assertEqual(response['X-Robots-Tag'], 'noindex')

    def test_export_name_with_different_case(self):
        """Test export with different case in page name."""
        url = href('wiki', self.page_name.upper(), 'a', 'export', 'raw')
        response = self.client.get(url, follow=True)

        # Should redirect to normalized name
        self.assertRedirects(response, f'/{self.page_name}/a/export/raw/')

    def test_export_without_read_privilege(self):
        """Test export without read privilege requires login."""
        self.client.logout()

        # Create ACL that denies read access
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

        url = self.page.get_absolute_url('export', format='raw')
        response = self.client.get(url, follow=True)

        # Should redirect to login
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertTrue(
            response.redirect_chain[0][0].startswith(href('portal', 'login')))

    def test_export_multiline_content_raw(self):
        """Test exporting raw content with multiple lines."""
        multiline_text = 'line 1\nline 2\nline 3'
        self.page.edit(text=multiline_text, user=self.user, note='Multiline')

        url = self.page.get_absolute_url('export', format='raw')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'line 1', response.content)
        self.assertIn(b'line 2', response.content)
        self.assertIn(b'line 3', response.content)

    def test_export_special_characters_raw(self):
        """Test exporting raw content with special characters."""
        special_text = 'Special chars: äöü, €, @#$%'
        self.page.edit(text=special_text, user=self.user, note='Special')

        url = self.page.get_absolute_url('export', format='raw')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn('äöü'.encode('utf-8'), response.content)

    def test_export_revision_isdigit_boundary(self):
        """Test export with revision that starts with digit but has non-digit chars."""
        url = self.page.get_absolute_url('export', format='raw', revision='123abc')
        response = self.client.get(url)

        # '123abc'.isdigit() is False, so should get latest revision
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'initial content', response.content)

    def test_export_html_and_raw_both_set_robots_tag(self):
        """Test that both raw and html formats set X-Robots-Tag."""
        url_raw = self.page.get_absolute_url('export', format='raw')
        url_html = self.page.get_absolute_url('export', format='html')

        response_raw = self.client.get(url_raw)
        response_html = self.client.get(url_html)

        self.assertEqual(response_raw['X-Robots-Tag'], 'noindex')
        self.assertEqual(response_html['X-Robots-Tag'], 'noindex')

    def test_export_multiple_revisions_raw(self):
        """Test exporting multiple different revisions in raw format."""
        self.page.edit(text='rev 1', user=self.user, note='Edit 1')
        self.page.edit(text='rev 2', user=self.user, note='Edit 2')

        revisions = self.page.revisions.all().order_by('id')

        # Export second revision
        rev_id = revisions[1].id
        url = self.page.get_absolute_url('export', format='raw', revision=rev_id)
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'rev 1', response.content)
        self.assertNotIn(b'rev 2', response.content)


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
