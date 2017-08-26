from django.conf import settings
from django.contrib.auth.models import Group
from django.core.cache import cache
from guardian.shortcuts import assign_perm, remove_perm

from inyoka.forum.models import (
    Forum,
    Topic,
)
from inyoka.portal.models import Subscription
from inyoka.portal.user import User
from inyoka.utils.test import AntiSpamTestCaseMixin, InyokaClient, TestCase


class TestSubscription(AntiSpamTestCaseMixin, TestCase):

    client_class = InyokaClient

    def setUp(self):
        super(TestSubscription, self).setUp()
        self.client.defaults['HTTP_HOST'] = 'forum.%s' % settings.BASE_DOMAIN_NAME

        self.user = User.objects.register_user('user', 'user@example.com', 'user', False)
        self.forum = Forum.objects.create(name='Forum')
        self.topic = Topic.objects.create(title='A test Topic', author=self.user,
                forum=self.forum)

        self.registered = Group.objects.get(name=settings.INYOKA_REGISTERED_GROUP_NAME)




    def test_subscribe(self):
        self.client.login(username='user', password='user')
        registered = Group.objects.get(name=settings.INYOKA_REGISTERED_GROUP_NAME)
        assign_perm('forum.view_forum', registered, self.forum)

        self.client.get('/topic/%s/subscribe/' % self.topic.slug)
        self.assertTrue(
            Subscription.objects.user_subscribed(self.user, self.topic))

        # Test for unsubscribe-link in the usercp if the user has no more read
        # access to a subscription
        remove_perm('forum.view_forum', registered, self.forum)
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
