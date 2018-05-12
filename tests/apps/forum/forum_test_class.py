from inyoka.forum.models import Forum, Topic, Post
from inyoka.portal.user import User
from inyoka.utils.test import TestCase


class ForumTestCase(TestCase):

    def setUp(self):
        super(ForumTestCase, self).setUp()
        self.user = User.objects.register_user('admin', 'admin', 'admin', False)

        self.parent1 = Forum.objects.create(
            name='This is a test')
        self.parent2 = Forum.objects.create(
            name='This is a second test',
            parent=self.parent1)
        self.forum = Forum.objects.create(
            name='This rocks damnit',
            parent=self.parent2)

        self.topic = Topic(title='topic', author=self.user, forum=self.forum)
        self.topic.save()

    def addPosts(self, number=1):
        for post_id in xrange(number):
            post = Post(text=u'test%s' % post_id, author=self.user, topic=self.topic)
            post.save()
            yield post
