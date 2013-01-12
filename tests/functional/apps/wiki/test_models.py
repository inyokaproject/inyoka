#-*- coding: utf-8 -*-
"""
    tests.functional.apps.wiki.test_models
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test wiki models.

    :copyright: (c) 2012-2013 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL.
"""
from django.test import TestCase

from inyoka.portal.user import User
from inyoka.wiki.models import Page


class TestModels(TestCase):
    def test_render_dynamic_macros(self):
        admin = User.objects.register_user('admin', 'admin', 'admin', False)
        p = Page.objects.create('BlaPage', '|[[PageName()]]|', user=admin, note='rev0')
        self.assertEqual('<p>|BlaPage|</p>', p.rev.rendered_text)
