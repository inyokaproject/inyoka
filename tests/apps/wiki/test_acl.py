# -*- coding: utf-8 -*-
"""
    test_wiki_acl
    ~~~~~~~~~~~~~

    Test the wiki acl.

    :copyright: Copyright 2007-2015 by the Inyoka-Team.
    :license: BSD, see LICENSE for more details.
"""
from django.test import TestCase

from inyoka.wiki.acl import *
from inyoka.wiki.models import Page
from inyoka.portal.user import User
from inyoka.utils.cache import request_cache


class TestWikiAcl(TestCase):
    def test_normalized_naming(self):
        user = User.objects.create_user('test normalized name', 'test2@example.com')
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
        Page.objects.create('ACL', test_page, user)

        self.assertEqual(get_privilege_flags('test normalized_name', 'some_page'), PRIV_ALL)

        self.assertEqual(get_privilege_flags('test normalized_name', 'page'), PRIV_READ)
        self.assertEqual(get_privilege_flags('test normalized_name', 'page_normalized1'), PRIV_READ)
        self.assertEqual(get_privilege_flags('test normalized_name', 'page_normalized2'), PRIV_READ)
        self.assertEqual(get_privilege_flags('test normalized_name', 'wild_cards1/test a'), PRIV_READ)
        self.assertEqual(get_privilege_flags('test normalized_name', 'wild_cards1/test b'), PRIV_READ)
        self.assertEqual(get_privilege_flags('test normalized_name', 'wild cards2/test a'), PRIV_READ)
        self.assertEqual(get_privilege_flags('test normalized_name', 'wild cards2/test b'), PRIV_READ)

        request_cache.delete('wiki/storage/Access-Control-List')
