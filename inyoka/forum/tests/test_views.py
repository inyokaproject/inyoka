#-*- coding: utf-8 -*-
from mock import patch

from django.conf import settings
from django.test import TestCase, Client
from django.test.utils import override_settings
from django.utils.translation import ugettext as _

from inyoka.utils.test import profile_memory
from inyoka.forum.acl import PRIVILEGES_BITS
from inyoka.forum.models import Forum, Topic, Post, Privilege
from inyoka.portal.user import User, PERMISSION_NAMES
from inyoka.utils.test import InyokaClient


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


class TestViews(TestCase):

    client_class = InyokaClient
    permissions = sum(PERMISSION_NAMES.keys())
    privileges = sum(PRIVILEGES_BITS.values())

    def setUp(self):
        self.admin = User.objects.register_user('admin', 'admin', 'admin', False)
        self.user = User.objects.register_user('user', 'user', 'user', False)
        self.admin._permissions = self.permissions
        self.admin.save()

        self.forum1 = Forum.objects.create(name='Forum 1')
        self.forum2 = Forum.objects.create(name='Forum 2', parent=self.forum1)
        self.forum3 = Forum.objects.create(name='Forum 3', parent=self.forum1)

        forums = [self.forum1, self.forum2, self.forum3]

        for f in forums:
            Privilege.objects.create(user=self.admin, forum=f,
                    positive=self.privileges, negative=0)

        self.topic = Topic.objects.create(title='A test Topic', author=self.user,
                forum=self.forum2)
        self.post = Post.objects.create(text=u'Post 1', author=self.user,
                topic=self.topic)

        self.client.defaults['HTTP_HOST'] = 'forum.%s' % settings.BASE_DOMAIN_NAME
        self.client.login(username='admin', password='admin')

    def test_reported_topics(self):
        response = self.client.get('/reported_topics/')
        self.assertEqual(response.status_code, 200)

    @patch('inyoka.middlewares.security.SecurityMiddleware._make_token',
            return_value = 'csrf_key')
    @patch('inyoka.forum.views.send_notification')
    def test_movetopic(self, mock_send, mock_security):
        self.assertEqual(Topic.objects.get(id=self.topic.id).forum_id,
                self.forum2.id)
        response = self.client.post('/topic/%s/move/' % self.topic.slug,
                    {'_form_token': 'csrf_key', 'forum': self.forum3.id})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(mock_send.call_count, 1) #only the topic author
        mock_send.assert_called_with(self.user, 'topic_moved',
            _(u'Your topic “%(topic)s“ was moved.') % {'topic': 'A test Topic'}, {
                'username': self.user.username, 'topic': self.topic,
                'mod': self.admin.username, 'forum_name': 'Forum 3',
                'old_forum_name': 'Forum 2'})

        self.assertEqual(Topic.objects.get(id=self.topic.id).forum_id,
                self.forum3.id)
