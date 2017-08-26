from django.conf import settings
from django.contrib.auth.models import Group
from django.core.cache import cache
from guardian.shortcuts import assign_perm, remove_perm

from inyoka.forum.models import (
    Forum,
    Post,
    Topic,
)
from inyoka.portal.models import Subscription
from inyoka.portal.user import User
from inyoka.utils.test import AntiSpamTestCaseMixin, InyokaClient, TestCase


class TestSubscription(AntiSpamTestCaseMixin, TestCase):

    client_class = InyokaClient

    def setUp(self):
        super(TestSubscription, self).setUp()
        self.admin = User.objects.register_user('admin', 'admin@example.com', 'admin', False)
        self.admin.is_superuser = True
        self.admin.save()

        self.user = User.objects.register_user('user', 'user@example.com', 'user', False)
        self.system_user = User.objects.get_system_user()

        self.forum1 = Forum.objects.create(name='Forum 1')
        self.forum2 = Forum.objects.create(name='Forum 2', parent=self.forum1)
        self.forum3 = Forum.objects.create(name='Forum 3', parent=self.forum1)

        self.topic = Topic.objects.create(title='A test Topic', author=self.user,
                forum=self.forum2)
        self.post = Post.objects.create(text=u'Post 1', author=self.user,
                topic=self.topic, position=0)

        self.client.defaults['HTTP_HOST'] = 'forum.%s' % settings.BASE_DOMAIN_NAME
        self.client.login(username='admin', password='admin')

    def tearDown(self):
        from inyoka.portal import user
        user._ANONYMOUS_USER = None
        user._SYSTEM_USER = None

    def test_subscribe(self):
        self.client.login(username='user', password='user')
        registered = Group.objects.get(name=settings.INYOKA_REGISTERED_GROUP_NAME)
        assign_perm('forum.view_forum', registered, self.forum2)

        self.client.get('/topic/%s/subscribe/' % self.topic.slug)
        self.assertTrue(
            Subscription.objects.user_subscribed(self.user, self.topic))

        # Test for unsubscribe-link in the usercp if the user has no more read
        # access to a subscription
        remove_perm('forum.view_forum', registered, self.forum2)
        cache.clear()
        response = self.client.get('/usercp/subscriptions/', {}, False,
                                   HTTP_HOST=settings.BASE_DOMAIN_NAME)
        self.assertTrue(
            ('/topic/%s/unsubscribe/?next=' % self.topic.slug)
            in response.content.decode("utf-8")
        )

        forward_url = 'http://%s/myfwd' % settings.BASE_DOMAIN_NAME
        response = self.client.get(
            '/topic/%s/unsubscribe/' % self.topic.slug,
            {'next': forward_url}
        )
        self.assertFalse(
            Subscription.objects.user_subscribed(self.user, self.topic))
        self.assertEqual(response['location'], forward_url)
