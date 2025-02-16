"""
    tests.apps.forum.test_services
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test forum services.

    :copyright: (c) 2012-2025 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.conf import settings

from inyoka.forum.models import Forum, Post, Topic
from inyoka.portal.user import User
from inyoka.utils.test import InyokaClient, TestCase


class TestForumServices(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()
        self.admin = User.objects.register_user('admin', 'admin@inyoka.test', 'admin', False)
        self.admin.is_superuser = True
        self.admin.save()

        self.user = User.objects.register_user('user', 'user@inyoka.test', 'user', False)
        self.system_user = User.objects.get_system_user()

        self.forum1 = Forum.objects.create(name='Forum 1')

        self.topic = Topic.objects.create(title='A test Topic', author=self.user,
                forum=self.forum1)
        self.post = Post.objects.create(text='Post 1', author=self.user,
                topic=self.topic, position=0)
        self.post2 = Post.objects.create(text='Post 2', author=self.user,
                                        topic=self.topic, position=0)

        self.client.defaults['HTTP_HOST'] = 'forum.%s' % settings.BASE_DOMAIN_NAME

    def test_get_new_latest_posts(self):
        self.client.login(username='admin', password='admin')

        response = self.client.post('/?__service__=forum.get_new_latest_posts', data={'post': self.post.id}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Post 2')

    def test_get_new_latest_posts__anonymous(self):
        response = self.client.post('/?__service__=forum.get_new_latest_posts', data={'post': self.post.id}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), 'null')
