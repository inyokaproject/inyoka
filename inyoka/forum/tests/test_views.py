#-*- coding: utf-8 -*-
from django.test import TestCase, Client
from django.test.utils import override_settings
from inyoka.utils.test import profile_memory


class TestForumViews(TestCase):

    @override_settings(BASE_DOMAIN_NAME='inyoka.local')
    def test_forum_index(self):
        client = Client(HTTP_HOST='forum.inyoka.local')
        resp = client.get('/')
        self.assertEqual(resp.status_code, 200)

    @override_settings(BASE_DOMAIN_NAME='inyoka.local')
    def test_forum_index_memory(self):
        client = Client(HTTP_HOST='forum.inyoka.local')
        @profile_memory
        def go():
            resp = client.get('/')
        go()
