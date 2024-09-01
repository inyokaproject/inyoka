from django.core.cache import cache

from inyoka.forum.models import Forum, Post, Topic
from inyoka.portal.user import User
from inyoka.utils.test import TestCase


class ForumTestCase(TestCase):

    def setUp(self):
        super().setUp()
        self.user = User.objects.register_user('admin', 'admin', 'admin', False)

        self.category = Forum.objects.create(
            name='category')
        self.parent = Forum.objects.create(
            name='parent',
            parent=self.category)
        self.forum = Forum.objects.create(
            name='forum',
            parent=self.parent)

        self.topic = Topic(title='topic', author=self.user, forum=self.forum)
        self.topic.save()

        self.topic_posts = list(self.addPosts(5))

        # Setup the cache
        cache.clear()
        self.user.post_count.db_count(write_cache=True)

    def addPosts(self, number=1, topic=None):
        if not topic:
            topic = self.topic

        for post_id in range(number):
            post = Post(text='test%s' % post_id, author=self.user, topic=topic)
            post.save()
            yield post


class ForumTestCaseWithSecondItems(ForumTestCase):

    def setUp(self):
        super().setUp()

        self.other_forum = Forum(name='forum2')
        self.other_forum.user_count_posts = False
        self.other_forum.save()

        self.other_topic = Topic(title='topic2', author=self.user, forum=self.other_forum)
        self.other_topic.save()

        self.other_topic_posts = list(self.addPosts(5, self.other_topic))
