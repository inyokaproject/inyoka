"""
tests.apps.wiki.test_service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test service-endpoints of the wiki.

:copyright: (c) 2007-2026 by the Inyoka Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from unittest.mock import Mock, patch

from inyoka.forum.models import Post as ForumPost
from inyoka.utils.test import TestCase
from inyoka.wiki.exceptions import CaseSensitiveException
from inyoka.wiki.models import Page


class TestRenderPreview(TestCase):
    def test_render_preview_without_page_or_post(self):
        response = self.client.post(
            '/?__service__=wiki.render_preview',
            {'text': 'Hello from preview'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), '<p>Hello from preview</p>')

    def test_render_preview_with_existing_page(self):
        page = Mock()
        with patch.object(Page.objects, 'get_by_name', return_value=page):
            response = self.client.post(
                '/?__service__=wiki.render_preview',
                {'page': 'Main', 'text': 'Page preview text'},
            )
        self.assertContains(response, 'Page preview text')

    def test_render_preview_with_missing_page(self):
        with patch.object(Page.objects, 'get_by_name', side_effect=Page.DoesNotExist):
            response = self.client.post(
                '/?__service__=wiki.render_preview',
                {'page': 'missing-page', 'text': 'Fallback page preview'},
            )
        self.assertContains(response, 'Fallback page preview')

    def test_render_preview_with_case_sensitive_exception(self):
        page = Mock()
        with patch.object(
            Page.objects,
            'get_by_name',
            side_effect=CaseSensitiveException(page=page),
        ):
            response = self.client.post(
                '/?__service__=wiki.render_preview',
                {'page': 'WrongCase', 'text': 'Case mismatch preview'},
            )
        self.assertContains(response, 'Case mismatch preview')

    def test_render_preview_with_existing_post(self):
        post = Mock()
        with patch.object(ForumPost.objects, 'get', return_value=post):
            response = self.client.post(
                '/?__service__=wiki.render_preview',
                {'post': 1, 'text': 'Forum post preview'},
            )
        self.assertContains(response, 'Forum post preview')

    def test_render_preview_with_missing_post(self):
        with patch.object(ForumPost.objects, 'get', side_effect=ForumPost.DoesNotExist):
            response = self.client.post(
                '/?__service__=wiki.render_preview',
                {'post': 999, 'text': 'Missing forum post preview'},
            )
        self.assertContains(response, 'Missing forum post preview')
