"""
    test_wiki_acl
    ~~~~~~~~~~~~~

    Test the wiki acl.

    :copyright: (c) 2012-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.core.cache import cache

from inyoka.portal.user import User
from inyoka.utils.test import TestCase
from inyoka.wiki.acl import PRIV_ALL, PRIV_READ, get_privilege_flags
from inyoka.wiki.models import Page


class TestWikiAcl(TestCase):
    def test_normalized_naming(self):
        user = User.objects.create_user('test_user', 'test2@example.com')
        test_page = """
#X-Behave: Access-Control-List
{{{
[*]
test_user=all

[page]
test_user=-edit,-create,-attach,-manage,-delete

[page normalized1]
test_user=-edit,-create,-attach,-manage,-delete

[page_normalized2]
test_user=-edit,-create,-attach,-manage,-delete

[wild cards1/*]
test_user=-edit,-create,-attach,-manage,-delete

[wild_cards2/*]
test_user=-edit,-create,-attach,-manage,-delete
}}}
"""
        Page.objects.create('ACL', test_page, user)

        self.assertEqual(get_privilege_flags('test_user', 'some_page'), PRIV_ALL)

        self.assertEqual(get_privilege_flags('test_user', 'page'), PRIV_READ)
        self.assertEqual(get_privilege_flags('test_user', 'page_normalized1'), PRIV_READ)
        self.assertEqual(get_privilege_flags('test_user', 'page_normalized2'), PRIV_READ)
        self.assertEqual(get_privilege_flags('test_user', 'wild_cards1/test a'), PRIV_READ)
        self.assertEqual(get_privilege_flags('test_user', 'wild_cards1/test b'), PRIV_READ)
        self.assertEqual(get_privilege_flags('test_user', 'wild cards2/test a'), PRIV_READ)
        self.assertEqual(get_privilege_flags('test_user', 'wild cards2/test b'), PRIV_READ)

        cache.delete('wiki/storage/Access-Control-List')
