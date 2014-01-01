#-*- coding: utf-8 -*-
"""
    tests.apps.forum.test_acl
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Test forum ACL.

    :copyright: (c) 2012-2014 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL.
"""
import unittest

from inyoka.forum import acl


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
