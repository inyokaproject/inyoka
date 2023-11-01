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
        super().setUp()
        self.client.defaults['HTTP_HOST'] = 'forum.%s' % settings.BASE_DOMAIN_NAME

        self.user = User.objects.register_user('user', 'user@example.com', 'user', False)
        self.forum = Forum.objects.create(name='Forum')
        self.topic = Topic.objects.create(title='A test Topic', author=self.user,
                                          forum=self.forum)

        self.registered = Group.objects.get(name=settings.INYOKA_REGISTERED_GROUP_NAME)
        self.client.login(username='user', password='user')

    def teardown(self):
        cache.clear()

    def test_should_subscribe_to_topic_if_user_has_permission(self):
        self.set_up_subscription_to_topic()

        self.assertTrue(Subscription.objects.user_subscribed(self.user, self.topic),
                        "The user should be a subscriber for this topic")

    def test_should_not_subscribe_to_topic_if_user_misses_permission(self):
        remove_perm('forum.view_forum', self.registered, self.forum)

        self.client.get('/topic/%s/subscribe/' % self.topic.slug)

        self.assertFalse(Subscription.objects.user_subscribed(self.user, self.topic),
                        "It shouldn't be possible to subscribe to topics which you can't view")

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

    def test_read_for_topic_sub_should_be_true_if_user_can_view_forum(self):
        assign_perm('forum.view_forum', self.registered, self.forum)

        subscription = Subscription(user = self.user, content_object=self.topic)

        self.assertTrue(subscription.can_read())

    def test_read_for_topic_sub_should_be_false_if_user_cannot_view_forum(self):
        remove_perm('forum.view_forum', self.registered, self.forum)

        subscription = Subscription(user = self.user, content_object=self.topic)

        self.assertFalse(subscription.can_read())

    def test_read_for_version_should_be_true_if_user_can_view_forum(self):
        assign_perm('forum.view_forum', self.registered, self.forum)

        subscription = Subscription(user=self.user, content_object=None)

        self.assertTrue(subscription.can_read(forum_id=self.forum.id))

    def test_read_for_version_should_be_false_if_forum_id_is_missing(self):
        subscription = Subscription(user=self.user, content_object=None)

        self.assertFalse(subscription.can_read())

    def test_read_for_version_should_be_false_if_user_cannot_view_forum(self):
        remove_perm('forum.view_forum', self.registered, self.forum)

        subscription = Subscription(user=self.user, content_object=None)

        self.assertFalse(subscription.can_read(forum_id=self.forum.id))

    def test_read_for_forum_should_be_true_if_user_can_view_forum(self):
        assign_perm('forum.view_forum', self.registered, self.forum)

        subscription = Subscription(user=self.user, content_object=self.forum)

        self.assertTrue(subscription.can_read())

    def test_read_for_forum_should_be_false_if_user_cannot_view_forum(self):
        remove_perm('forum.view_forum', self.registered, self.forum)

        subscription = Subscription(user=self.user, content_object=self.forum)

        self.assertFalse(subscription.can_read())

    def test_read_for_user_should_be_true_if_user_can_subscribe_to_users(self):
        assign_perm('portal.subscribe_user', self.registered)
        other_user = User()

        subscription = Subscription(user=self.user, content_object=other_user)

        self.assertTrue(subscription.can_read())

    def test_read_for_user_should_be_false_if_user_cannot_subscribe_to_users(self):
        remove_perm('portal.subscribe_user', self.registered)
        other_user = User()

        subscription = Subscription(user=self.user, content_object=other_user)

        self.assertFalse(subscription.can_read())
