#-*- coding: utf-8 -*-
"""
    tests.apps.forum.test_views
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test forum views.

    :copyright: (c) 2012-2013 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL.
"""
from django.conf import settings
from django.core import mail
from django.test import TestCase
from django.utils import translation

from inyoka.forum.acl import CAN_READ, PRIVILEGES_BITS
from inyoka.forum.models import Forum, Topic, Post, Privilege
from inyoka.forum.notifications import send_move_notification, \
    send_reported_topics_notification, send_split_notification
from inyoka.portal.models import Subscription
from inyoka.portal.user import User, PERMISSION_NAMES
from inyoka.utils.storage import storage
from inyoka.utils.test import InyokaClient


class TestNotifications(TestCase):

    client_class = InyokaClient
    permissions = sum(PERMISSION_NAMES.keys())
    privileges = sum(PRIVILEGES_BITS.values())

    def setUp(self):
        self.admin = User.objects.register_user('admin', 'admin@example.com', 'admin', False)
        self.admin2 = User.objects.register_user('admin2', 'admin2@example.com', 'admin2', False)
        self.user = User.objects.register_user('user', 'user@example.com', 'user', False)
        self.user2 = User.objects.register_user('user2', 'user2@example.com', 'user2', False)
        self.user_no_read = User.objects.register_user('user_no_read', 'user_nr@example.com', 'user_no_read', False)
        self.admin._permissions = self.permissions
        self.admin.save()
        self.admin2._permissions = self.permissions
        self.admin2.save()

        self.forum1 = Forum.objects.create(name='Forum 1')
        self.forum2 = Forum.objects.create(name='Forum 2', parent=self.forum1)
        self.forums = [self.forum1, self.forum2]

        for f in self.forums:
            Privilege.objects.create(user=self.admin, forum=f, positive=self.privileges, negative=0)
            Privilege.objects.create(user=self.admin2, forum=f, positive=self.privileges, negative=0)
            Privilege.objects.create(user=self.user, forum=f, positive=CAN_READ, negative=0)
            Privilege.objects.create(user=self.user2, forum=f, positive=CAN_READ, negative=0)

        self.topic = Topic.objects.create(title='A test Topic', author=self.user,
                forum=self.forum2)
        self.post = Post.objects.create(text=u'Post 1', author=self.user,
                topic=self.topic)

        self.client.defaults['HTTP_HOST'] = 'forum.%s' % settings.BASE_DOMAIN_NAME
        self.client.login(username='user', password='user')

    def tearDown(self):
        # Make sure to clean the mail outbox after each test
        mail.outbox = []

    def test_report(self):
        subscribers = [self.admin.pk, self.admin2.pk]
        storage['reported_topics_subscribers'] = ','.join(str(i) for i in subscribers)

        self.topic.reported = 'some long reason: Lorem ipsum dolor sit ' \
            'amet, consectetur adipisicing elit, sed do eiusmod tempor.'
        self.topic.reporter_id = self.user.pk
        self.topic.save(update_fields=['reported', 'reporter_id'])
        with translation.override('en-us'):
            send_reported_topics_notification(self.topic)

        self.assertEqual(len(mail.outbox), 2)

        mail1, mail2 = mail.outbox[0], mail.outbox[1]
        self.assertIn(u'Hello admin,', mail1.body)
        self.assertIn(u'user reported', mail1.body)
        self.assertIn(u'topic “A test Topic”', mail1.body)
        self.assertIn(u'(http://forum.inyoka.local/topic/a-test-topic/)', mail1.body)
        self.assertIn(u'forum “Forum 2”.', mail1.body)
        self.assertIn(u'    some long reason: Lorem ', mail1.body)
        self.assertIn(u'    sed do eiusmod', mail1.body)
        self.assertIn(u'http://forum.inyoka.local/reported_topics/', mail1.body)
        self.assertEqual(mail1.to, [u'admin@example.com'])
        self.assertEqual(mail1.subject, u'ubuntuusers.de: Reported topic: “A test Topic”')

        self.assertIn(u'Hello admin2,', mail2.body)
        self.assertIn(u'user reported', mail2.body)
        self.assertIn(u'topic “A test Topic”', mail2.body)
        self.assertIn(u'(http://forum.inyoka.local/topic/a-test-topic/)', mail2.body)
        self.assertIn(u'forum “Forum 2”.', mail2.body)
        self.assertIn(u'    some long reason: Lorem ', mail2.body)
        self.assertIn(u'    sed do eiusmod', mail2.body)
        self.assertIn(u'http://forum.inyoka.local/reported_topics/', mail2.body)
        self.assertEqual(mail2.to, [u'admin2@example.com'])
        self.assertEqual(mail2.subject, u'ubuntuusers.de: Reported topic: “A test Topic”')

    def test_movetopic(self):
        for u in [self.admin, self.admin2, self.user, self.user2, self.user_no_read]:
            Subscription(user=u, content_object=self.topic).save()
            for f in self.forums:
                Subscription(user=u, content_object=f).save()

        with translation.override('en-us'):
            send_move_notification(self.topic, self.forum1, self.forum2, self.admin)

        self.assertEqual(len(mail.outbox), 3)

        mail1, mail2, mail3 = mail.outbox[0], mail.outbox[1], mail.outbox[2]
        self.assertIn(u'Hello user,', mail1.body)
        self.assertIn(u'admin moved', mail1.body)
        self.assertIn(u'topic “A test Topic”', mail1.body)
        self.assertIn(u'http://forum.inyoka.local/topic/a-test-topic/', mail1.body)
        self.assertIn(u'from the forum “Forum 1” to “Forum 2”.', mail1.body)
        self.assertEqual(mail1.to, [u'user@example.com'])
        self.assertEqual(mail1.subject, u'ubuntuusers.de: Your topic “A test Topic” was moved')

        self.assertIn(u'Hello admin2,', mail2.body)
        self.assertIn(u'admin moved', mail2.body)
        self.assertIn(u'topic “A test Topic”', mail2.body)
        self.assertIn(u'http://forum.inyoka.local/topic/a-test-topic/', mail2.body)
        self.assertIn(u'from the forum “Forum 1” to “Forum 2”.', mail2.body)
        self.assertEqual(mail2.to, [u'admin2@example.com'])
        self.assertEqual(mail2.subject, u'ubuntuusers.de: The topic “A test Topic” was moved')

        self.assertIn(u'Hello user2,', mail3.body)
        # Since the other body parts didn't change from mail1 -> mail2, skip them here
        self.assertEqual(mail3.to, [u'user2@example.com'])
        self.assertEqual(mail3.subject, u'ubuntuusers.de: The topic “A test Topic” was moved')

    def test_splittopic_new(self):
        new_topic = Topic.objects.create(title='New Topic', author=self.user,
                forum=self.forum2)
        Post.objects.create(text=u'Post 2', author=self.user, topic=new_topic)
        Post.objects.create(text=u'Post 3', author=self.user, topic=new_topic)

        for u in [self.admin, self.admin2, self.user, self.user2, self.user_no_read]:
            Subscription(user=u, content_object=self.topic).save()
            for f in self.forums:
                Subscription(user=u, content_object=f).save()

        with translation.override('en-us'):
            send_split_notification(self.topic, new_topic, True, self.admin)

        self.assertEqual(len(mail.outbox), 3)

        mail1, mail2, mail3 = mail.outbox[0], mail.outbox[1], mail.outbox[2]
        self.assertIn(u'Hello admin2,', mail1.body)
        self.assertIn(u'admin has split', mail1.body)
        self.assertIn(u'topic “A test Topic”', mail1.body)
        self.assertIn(u'to “New Topic”', mail1.body)
        self.assertIn(u'splited part by visiting http://forum.inyoka.local/topic/new-topic/', mail1.body)
        self.assertIn(u'original topic by visiting http://forum.inyoka.local/topic/a-test-topic/', mail1.body)
        self.assertEqual(mail1.to, [u'admin2@example.com'])
        self.assertEqual(mail1.subject, u'ubuntuusers.de: The topic “A test Topic” was split')

        self.assertIn(u'Hello user,', mail2.body)
        self.assertIn(u'admin has split', mail2.body)
        self.assertIn(u'topic “A test Topic”', mail2.body)
        self.assertIn(u'to “New Topic”', mail2.body)
        self.assertIn(u'splited part by visiting http://forum.inyoka.local/topic/new-topic/', mail2.body)
        self.assertIn(u'original topic by visiting http://forum.inyoka.local/topic/a-test-topic/', mail2.body)
        self.assertEqual(mail2.to, [u'user@example.com'])
        self.assertEqual(mail2.subject, u'ubuntuusers.de: The topic “A test Topic” was split')

        self.assertIn(u'Hello user2,', mail3.body)
        # Since the other body parts didn't change from mail1 -> mail2, skip them here
        self.assertEqual(mail3.to, [u'user2@example.com'])
        self.assertEqual(mail3.subject, u'ubuntuusers.de: The topic “A test Topic” was split')

    def test_splittopic_append(self):
        new_topic = Topic.objects.create(title='New Topic', author=self.user,
                forum=self.forum2)
        Post.objects.create(text=u'Post 2', author=self.user, topic=new_topic)
        Post.objects.create(text=u'Post 3', author=self.user, topic=new_topic)

        for u in [self.admin, self.admin2, self.user, self.user2, self.user_no_read]:
            Subscription(user=u, content_object=self.topic).save()
            for f in self.forums:
                Subscription(user=u, content_object=f).save()

        with translation.override('en-us'):
            send_split_notification(self.topic, new_topic, True, self.admin)

        self.assertEqual(len(mail.outbox), 3)

        mail1, mail2, mail3 = mail.outbox[0], mail.outbox[1], mail.outbox[2]
        self.assertIn(u'Hello admin2,', mail1.body)
        self.assertIn(u'admin has split', mail1.body)
        self.assertIn(u'topic “A test Topic”', mail1.body)
        self.assertIn(u'to “New Topic”', mail1.body)
        self.assertIn(u'splited part by visiting http://forum.inyoka.local/topic/new-topic/', mail1.body)
        self.assertIn(u'original topic by visiting http://forum.inyoka.local/topic/a-test-topic/', mail1.body)
        self.assertEqual(mail1.to, [u'admin2@example.com'])
        self.assertEqual(mail1.subject, u'ubuntuusers.de: The topic “A test Topic” was split')

        self.assertIn(u'Hello user,', mail2.body)
        self.assertIn(u'admin has split', mail2.body)
        self.assertIn(u'topic “A test Topic”', mail2.body)
        self.assertIn(u'to “New Topic”', mail2.body)
        self.assertIn(u'splited part by visiting http://forum.inyoka.local/topic/new-topic/', mail2.body)
        self.assertIn(u'original topic by visiting http://forum.inyoka.local/topic/a-test-topic/', mail2.body)
        self.assertEqual(mail2.to, [u'user@example.com'])
        self.assertEqual(mail2.subject, u'ubuntuusers.de: The topic “A test Topic” was split')

        self.assertIn(u'Hello user2,', mail3.body)
        # Since the other body parts didn't change from mail1 -> mail2, skip them here
        self.assertEqual(mail3.to, [u'user2@example.com'])
        self.assertEqual(mail3.subject, u'ubuntuusers.de: The topic “A test Topic” was split')
