from django.test import TestCase
from django.test.utils import override_settings

from inyoka.forum import acl
from inyoka.forum.models import Forum, Topic, Post
from inyoka.portal.user import User


class TestForumAcl(TestCase):

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
