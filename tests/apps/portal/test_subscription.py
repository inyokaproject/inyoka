from django.conf import settings
from django.contrib.auth.models import Group
from django.core.cache import cache
from guardian.shortcuts import assign_perm, remove_perm

from inyoka.forum.models import (
    Forum,
    Topic)
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
        self.client.login(username='user', password='user')

    def test_should_subscribe_to_topic_if_user_has_permission(self):
        self.set_up_subscription_to_topic()

        self.assertTrue(Subscription.objects.user_subscribed(self.user, self.topic),
                        "The user should be a subscriber for this topic")

    def test_should_contain_unsubscribe_link_in_subscription_list_if_user_has_no_view_permission(self):
        self.set_up_subscription_to_topic()
        remove_perm('forum.view_forum', self.registered, self.forum)
        cache.clear()

        response = self.client.get('/usercp/subscriptions/', {}, False, HTTP_HOST=settings.BASE_DOMAIN_NAME)

        self.assertTrue(
            ('/topic/%s/unsubscribe/?next=' % self.topic.slug)
            in response.content.decode("utf-8")
        )

    def test_should_forward_to_defined_url_after_unsubcribe(self):
        self.set_up_subscription_to_topic()
        forward_url = 'http://%s/myfwd' % settings.BASE_DOMAIN_NAME

        response = self.client.get('/topic/%s/unsubscribe/' % self.topic.slug, {'next': forward_url})

        self.assertEqual(response['location'], forward_url)

    def test_should_unsubcribe_from_topic(self):
        self.set_up_subscription_to_topic()

        self.client.get('/topic/%s/unsubscribe/' % self.topic.slug)

        self.assertFalse(Subscription.objects.user_subscribed(self.user, self.topic))

    def set_up_subscription_to_topic(self):
        assign_perm('forum.view_forum', self.registered, self.forum)
        self.client.get('/topic/%s/subscribe/' % self.topic.slug)
