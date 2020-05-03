# -*- coding: utf-8 -*-
"""
    tests.apps.wiki.test_utils
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test the wiki utilities.

    :copyright: (c) 2007-2020 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from inyoka.utils.test import TestCase
from inyoka.wiki.exceptions import CircularRedirectException
from inyoka.wiki.models import Page
from inyoka.wiki.utils import get_safe_redirect_target


class TestWikiUtils(TestCase):

    def test_multiple_redirect(self):
        Page.objects.create(name='redirect_a', text='# X-Redirect: redirect_b')
        Page.objects.create(name='redirect_b', text='# X-Redirect: redirect_c')
        Page.objects.create(name='redirect_c', text='Test')
        self.assertEqual(get_safe_redirect_target('redirect_a'),
                         ('redirect_c', None))

    def test_multiple_redirect_with_anchors(self):
        Page.objects.create(name='anchor_a', text='# X-Redirect: anchor_b#b')
        Page.objects.create(name='anchor_b', text='# X-Redirect: anchor_c#c')
        Page.objects.create(name='anchor_c', text='Test')
        self.assertEqual(get_safe_redirect_target('anchor_a'),
                         ('anchor_c', 'c'))

    def test_circular_redirect(self):
        Page.objects.create(name='circular_a', text='# X-Redirect: circular_b')
        Page.objects.create(name='circular_b', text='# X-Redirect: circular_c')
        Page.objects.create(name='circular_c', text='# X-Redirect: circular_a')
        with self.assertRaises(CircularRedirectException):
            get_safe_redirect_target('circular_a')
