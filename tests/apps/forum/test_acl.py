#-*- coding: utf-8 -*-
"""
    tests.apps.forum.test_acl
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Test forum ACL.

    :copyright: (c) 2012-2015 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import unittest

from django.conf import settings
from django.core.cache import cache
from django.db.models.query import EmptyQuerySet

from inyoka.forum import acl
from inyoka.forum.models import Forum, Privilege
from inyoka.portal.user import DEFAULT_GROUP_ID, Group, User
from inyoka.utils.test import TestCase


class TestForumAcl(unittest.TestCase):

    def test_privileges_constant(self):
        self.assertEqual(acl.PRIVILEGES,
                         ['read', 'vote', 'create', 'reply',
                          'upload', 'create_poll', 'sticky',
                          'moderate'])

    def test_privileges_bits_constant(self):
        self.assertEqual(acl.PRIVILEGES_BITS,
            {'read': 2,
             'vote': 4,
             'create': 8,
             'reply': 16,
             'upload': 32,
             'create_poll': 64,
             'sticky': 128,
             'moderate': 256})

    def test_privileges_sugar_constants(self):
        self.assertEqual(acl.DISALLOW_ALL, 0)
        self.assertEqual(acl.PRIVILEGES_BITS['read'], acl.CAN_READ)
        self.assertEqual(acl.PRIVILEGES_BITS['vote'], acl.CAN_VOTE)
        self.assertEqual(acl.PRIVILEGES_BITS['create'], acl.CAN_CREATE)
        self.assertEqual(acl.PRIVILEGES_BITS['reply'], acl.CAN_REPLY)
        self.assertEqual(acl.PRIVILEGES_BITS['upload'], acl.CAN_UPLOAD)
        self.assertEqual(acl.PRIVILEGES_BITS['create_poll'], acl.CAN_CREATE_POLL)
        self.assertEqual(acl.PRIVILEGES_BITS['sticky'], acl.CAN_STICKY)
        self.assertEqual(acl.PRIVILEGES_BITS['moderate'], acl.CAN_MODERATE)

    def test_join_flags(self):
        self.assertEqual(acl.join_flags(), acl.DISALLOW_ALL)
        self.assertEqual(acl.join_flags(acl.CAN_READ, acl.CAN_CREATE, acl.CAN_REPLY),
                         26)
        # convenience method to join by name
        self.assertEqual(acl.join_flags('read', 'create', 'reply'), 26)
        # once DISALLOW_ALL is there, everything get's disallowed
        self.assertEqual(acl.join_flags('read', 'create', 'reply', acl.DISALLOW_ALL), 0)

    def test_split_bits(self):
        self.assertEqual(list(acl.split_bits()), [])
        self.assertEqual(list(acl.split_bits(None)), [])
        self.assertEqual(list(acl.split_bits(26)), [2, 8, 16])

    def test_split_negative_positive(self):
        self.assertEqual(acl.split_negative_positive('-2,-8,8'),
                         (10, 8))
        # ignores invalid numbers
        self.assertEqual(acl.split_negative_positive('-2,-8,something,8'),
                         (10, 8))


class TestForumPrivileges(TestCase):

    @classmethod
    def setUpClass(cls):
        Group.objects.create(id=DEFAULT_GROUP_ID, name='Registered')

    def setUp(self):
        self.user = User.objects.register_user('user', 'user@example.com', 'user', False)
        self.anonymous = User.objects.get_anonymous_user()
        self.client.defaults['HTTP_HOST'] = 'forum.%s' % settings.BASE_DOMAIN_NAME

    def tearDown(self):
        from inyoka.portal import user
        cache.clear()
        cache.clear()
        user._ANONYMOUS_USER = None

    @classmethod
    def tearDownClass(cls):
        Group.objects.filter(id=DEFAULT_GROUP_ID).delete()

    def test_no_forums(self):
        # test for anonymous
        self.assertEqual(acl.get_privileges(self.anonymous, None), {})
        self.assertEqual(acl.get_privileges(self.anonymous, []), {})
        self.assertEqual(acl.get_privileges(self.anonymous, ()), {})
        self.assertEqual(acl.get_privileges(self.anonymous, EmptyQuerySet), {})

        # test for user
        self.assertEqual(acl.get_privileges(self.user, None), {})
        self.assertEqual(acl.get_privileges(self.user, []), {})
        self.assertEqual(acl.get_privileges(self.user, ()), {})
        self.assertEqual(acl.get_privileges(self.user, EmptyQuerySet), {})

    def test_no_explicit_permissions(self):
        category = Forum.objects.create(name='Category')
        forum = Forum.objects.create(name='Forum 1', parent=category)
        privs = {
            category.pk: acl.DISALLOW_ALL,
            forum.pk: acl.DISALLOW_ALL,
        }
        # test for anonymous
        self.assertEqual(acl.get_privileges(self.anonymous, [category, forum]), privs)
        cache.clear()
        self.assertEqual(acl.get_privileges(self.anonymous, (category, forum)), privs)
        cache.clear()
        self.assertEqual(acl.get_privileges(self.anonymous, Forum.objects.all()), privs)
        cache.clear()

        # test for user
        self.assertEqual(acl.get_privileges(self.user, [category, forum]), privs)
        cache.clear()
        self.assertEqual(acl.get_privileges(self.user, (category, forum)), privs)
        cache.clear()
        self.assertEqual(acl.get_privileges(self.user, Forum.objects.all()), privs)

    def test_default_group_permissions(self):
        category = Forum.objects.create(name='Category')
        forum = Forum.objects.create(name='Forum 1', parent=category)
        Privilege.objects.create(group_id=DEFAULT_GROUP_ID, forum=category, positive=acl.CAN_READ)
        Privilege.objects.create(group_id=DEFAULT_GROUP_ID, forum=forum, positive=acl.CAN_VOTE)
        privs = {
            category.pk: acl.DISALLOW_ALL,
            forum.pk: acl.DISALLOW_ALL,
        }
        # test for anonymous
        self.assertEqual(acl.get_privileges(self.anonymous, [category, forum]), privs)
        cache.clear()
        self.assertEqual(acl.get_privileges(self.anonymous, (category, forum)), privs)
        cache.clear()
        self.assertEqual(acl.get_privileges(self.anonymous, Forum.objects.all()), privs)
        cache.clear()

        privs = {
            category.pk: acl.CAN_READ,
            forum.pk: acl.CAN_VOTE,
        }
        # test for user
        self.assertEqual(acl.get_privileges(self.user, [category, forum]), privs)
        cache.clear()
        self.assertEqual(acl.get_privileges(self.user, (category, forum)), privs)
        cache.clear()
        self.assertEqual(acl.get_privileges(self.user, Forum.objects.all()), privs)

    def test_explicit_user_permissions(self):
        category = Forum.objects.create(name='Category')
        forum = Forum.objects.create(name='Forum 1', parent=category)
        Privilege.objects.create(user=self.anonymous, forum=category, positive=acl.CAN_READ)
        Privilege.objects.create(user=self.anonymous, forum=forum, positive=acl.CAN_VOTE)
        Privilege.objects.create(user=self.user, forum=category, positive=acl.CAN_CREATE)
        Privilege.objects.create(user=self.user, forum=forum, positive=acl.CAN_REPLY)
        privs = {
            category.pk: acl.CAN_READ,
            forum.pk: acl.CAN_VOTE,
        }
        # test for anonymous
        self.assertEqual(acl.get_privileges(self.anonymous, [category, forum]), privs)
        cache.clear()
        self.assertEqual(acl.get_privileges(self.anonymous, (category, forum)), privs)
        cache.clear()
        self.assertEqual(acl.get_privileges(self.anonymous, Forum.objects.all()), privs)
        cache.clear()

        privs = {
            category.pk: acl.CAN_CREATE,
            forum.pk: acl.CAN_REPLY,
        }
        # test for user
        self.assertEqual(acl.get_privileges(self.user, [category, forum]), privs)
        cache.clear()
        self.assertEqual(acl.get_privileges(self.user, (category, forum)), privs)
        cache.clear()
        self.assertEqual(acl.get_privileges(self.user, Forum.objects.all()), privs)

    def test_explicit_user_permissions_with_default_group(self):
        category = Forum.objects.create(name='Category')
        forum = Forum.objects.create(name='Forum 1', parent=category)
        Privilege.objects.create(user=self.anonymous, forum=category, positive=acl.CAN_READ)
        Privilege.objects.create(user=self.anonymous, forum=forum, positive=acl.CAN_VOTE)
        Privilege.objects.create(user=self.user, forum=category, positive=acl.CAN_CREATE)
        Privilege.objects.create(user=self.user, forum=forum, positive=acl.CAN_REPLY)
        Privilege.objects.create(group_id=DEFAULT_GROUP_ID, forum=category, positive=acl.CAN_STICKY)
        Privilege.objects.create(group_id=DEFAULT_GROUP_ID, forum=forum, positive=acl.CAN_MODERATE)
        privs = {
            category.pk: acl.CAN_READ,
            forum.pk: acl.CAN_VOTE,
        }
        # test for anonymous
        self.assertEqual(acl.get_privileges(self.anonymous, [category, forum]), privs)
        cache.clear()
        self.assertEqual(acl.get_privileges(self.anonymous, (category, forum)), privs)
        cache.clear()
        self.assertEqual(acl.get_privileges(self.anonymous, Forum.objects.all()), privs)
        cache.clear()

        privs = {
            category.pk: acl.CAN_CREATE | acl.CAN_STICKY,
            forum.pk: acl.CAN_REPLY | acl.CAN_MODERATE,
        }
        # test for user
        self.assertEqual(acl.get_privileges(self.user, [category, forum]), privs)
        cache.clear()
        self.assertEqual(acl.get_privileges(self.user, (category, forum)), privs)
        cache.clear()
        self.assertEqual(acl.get_privileges(self.user, Forum.objects.all()), privs)

    def test_explicit_user_permissions_with_default_group_pos_neg(self):
        category = Forum.objects.create(name='Category')
        forum1 = Forum.objects.create(name='Forum 1', parent=category)
        forum2 = Forum.objects.create(name='Forum 2', parent=category)
        Privilege.objects.create(user=self.anonymous, forum=category, positive=acl.CAN_READ)
        Privilege.objects.create(user=self.anonymous, forum=forum1, positive=acl.CAN_VOTE)
        Privilege.objects.create(user=self.user, forum=category, positive=acl.CAN_READ)
        Privilege.objects.create(user=self.user, forum=forum1, positive=acl.CAN_READ)
        Privilege.objects.create(user=self.user, forum=forum2, positive=acl.CAN_READ | acl.CAN_REPLY)
        Privilege.objects.create(group_id=DEFAULT_GROUP_ID, forum=category, positive=acl.CAN_CREATE)
        Privilege.objects.create(group_id=DEFAULT_GROUP_ID, forum=forum1, negative=acl.CAN_MODERATE)

        # XXX: I'd have expected a acl.CAN_READ here, but since user privileges
        # override group privileges this does not work.
        Privilege.objects.create(group_id=DEFAULT_GROUP_ID, forum=forum2, negative=acl.CAN_REPLY)

        privs = {
            category.pk: acl.CAN_READ,
        }
        # test for anonymous
        self.assertEqual(acl.get_privileges(self.anonymous, [category]), privs)
        cache.clear()
        self.assertEqual(acl.get_privileges(self.anonymous, (category,)), privs)
        cache.clear()
        self.assertEqual(acl.get_privileges(self.anonymous, Forum.objects.filter(parent__isnull=True)), privs)
        cache.clear()

        privs = {
            forum1.pk: acl.CAN_VOTE,
            forum2.pk: acl.DISALLOW_ALL,
        }
        # test for anonymous
        self.assertEqual(acl.get_privileges(self.anonymous, [forum1, forum2]), privs)
        cache.clear()
        self.assertEqual(acl.get_privileges(self.anonymous, (forum1, forum2)), privs)
        cache.clear()
        self.assertEqual(acl.get_privileges(self.anonymous, Forum.objects.filter(parent__isnull=False)), privs)
        cache.clear()

        privs = {
            category.pk: acl.CAN_READ | acl.CAN_CREATE,
        }

        self.assertEqual(acl.get_privileges(self.user, [category]), privs)
        cache.clear()
        self.assertEqual(acl.get_privileges(self.user, (category,)), privs)
        cache.clear()
        self.assertEqual(acl.get_privileges(self.user, Forum.objects.filter(parent__isnull=True)), privs)

        privs = {
            forum1.pk: acl.CAN_READ,
            forum2.pk: acl.CAN_READ | acl.CAN_REPLY,
        }
        # test for user
        self.assertEqual(acl.get_privileges(self.user, [forum1, forum2]), privs)
        cache.clear()
        self.assertEqual(acl.get_privileges(self.user, (forum1, forum2)), privs)
        cache.clear()
        self.assertEqual(acl.get_privileges(self.user, Forum.objects.filter(parent__isnull=False)), privs)
        cache.clear()

        privs = {
            category.pk: acl.CAN_READ | acl.CAN_CREATE,
        }
        # test for user
        self.assertEqual(acl.get_privileges(self.user, [category]), privs)
        cache.clear()
        self.assertEqual(acl.get_privileges(self.user, (category,)), privs)
        cache.clear()
        self.assertEqual(acl.get_privileges(self.user, Forum.objects.filter(parent__isnull=True)), privs)
        cache.clear()

        privs = {
            forum1.pk: acl.CAN_READ,
            forum2.pk: acl.CAN_READ | acl.CAN_REPLY,
        }
        self.assertEqual(acl.get_privileges(self.user, [forum1, forum2]), privs)
        cache.clear()
        self.assertEqual(acl.get_privileges(self.user, (forum1, forum2)), privs)
        cache.clear()
        self.assertEqual(acl.get_privileges(self.user, Forum.objects.filter(parent__isnull=False)), privs)
        cache.clear()

        Privilege.objects.create(user=self.user, forum=category, negative=acl.CAN_CREATE)
        privs = {
            category.pk: acl.CAN_READ,
        }
        self.assertEqual(acl.get_privileges(self.user, [category]), privs)
        cache.clear()
        self.assertEqual(acl.get_privileges(self.user, (category,)), privs)
        cache.clear()
        self.assertEqual(acl.get_privileges(self.user, Forum.objects.filter(parent__isnull=True)), privs)
