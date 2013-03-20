# -*- coding: utf-8 -*-
"""
    test_wiki_acl
    ~~~~~~~~~~~~~

    Test the wiki acl.

    :copyright: Copyright 2007-2013 by the Inyoka-Team.
    :license: GNU GPL.
"""
from django.test import TestCase

from inyoka.portal.user import User
from inyoka.wiki.models import Page
from inyoka.wiki.acl import *
from inyoka.utils.cache import request_cache


class TestWikiAcl(TestCase):
    def test_normalized_naming(self):
        User.objects.create_user('test normalized name', 'test2@example.com')
        test_page = """
#X-Behave: Access-Control-List
{{{
[*]
test normalized name=all

[page]
test normalized name=-edit,-create,-attach,-manage,-delete

[page normalized1]
test normalized name=-edit,-create,-attach,-manage,-delete

[page_normalized2]
test_normalized_name=-edit,-create,-attach,-manage,-delete

[wild cards1/*]
test normalized name=-edit,-create,-attach,-manage,-delete

[wild_cards2/*]
test_normalized_name=-edit,-create,-attach,-manage,-delete
}}}
"""
        Page.objects.create('ACL', test_page)

        self.assertEqual(get_privilege_flags('test normalized_name', 'some_page'), PRIV_ALL)

        tests = (
            'page',

            'page_normalized1',
            'page normalized2',

            'wild_cards1/test a',
            'wild_cards1/test_a',

            'wild cards2/test a',
            'wild cards2/test_a',
        )

        for test in tests:
            self.assertEqual(get_privilege_flags('test normalized_name', test), PRIV_READ)

        request_cache.delete('wiki/storage/Access-Control-List')
