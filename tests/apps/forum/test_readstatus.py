from inyoka.forum.models import (
    Forum,
    Topic, ReadStatus, mark_all_forums_read, Post)
from inyoka.portal.user import User
from inyoka.utils.test import InyokaClient, TestCase


class TestReadStatus(TestCase):
    client_class = InyokaClient

    def setUp(self):
        super(TestReadStatus, self).setUp()

        self.reading_user = User.objects.register_user('user', 'user@example.com', 'user', False)
        self.posting_user = User.objects.register_user('user2', 'user2@example.com', 'user2', False)

        self.parent = Forum.objects.create(name='Parent')
        self.forum = Forum.objects.create(name='Forum', parent=self.parent)
        self.topic = Topic.objects.create(title='A test Topic', author=self.posting_user, forum=self.forum)
        self.write_new_post(self.forum, self.topic)
        self.parent.last_post = self.forum.last_post

        self.read_status = ReadStatus(self.reading_user.forum_read_status)

    def write_new_post(self, forum, topic):
        post = Post.objects.create(text=u'Post 1', author=self.posting_user, topic=topic, position=topic.post_count())
        forum.last_post = post
        topic.last_post = post

    def teardown(self):
        mark_all_forums_read(self.reading_user)

    def test_should_be_false_if_topic_is_unread(self):
        self.assertFalse(self.read_status(self.topic))

    def test_should_be_true_if_topic_is_marked(self):
        self.read_status.mark(self.topic, self.reading_user)
        self.reading_user.save()

        self.assertTrue(self.read_status(self.topic))

    def test_should_be_false_if_forum_is_unread(self):
        self.assertFalse(self.read_status(self.forum))

    def test_should_be_true_if_forum_is_read(self):
        self.read_status.mark(self.forum, self.reading_user)
        self.reading_user.save()

        self.assertTrue(self.read_status(self.forum))

    def test_should_be_true_for_topic_if_parent_is_marked(self):
        self.read_status.mark(self.forum, self.reading_user)
        self.reading_user.save()

        self.assertTrue(self.read_status(self.topic))

    def test_should_be_true_for_forum_if_all_topics_are_marked(self):
        self.read_status.mark(self.topic, self.reading_user)
        self.reading_user.save()

        self.assertTrue(self.read_status(self.forum))

    def test_should_be_false_for_forum_if_only_last_topic_is_marked(self):
        other_topic = Topic.objects.create(title='A test Topic', author=self.posting_user, forum=self.forum)
        self.write_new_post(self.forum, other_topic)

        self.read_status.mark(other_topic, self.reading_user)
        self.reading_user.save()

        self.assertFalse(self.read_status(self.forum))

    def test_should_be_false_for_forum_if_not_last_topic_is_marked(self):
        other_topic = Topic.objects.create(title='A test Topic', author=self.posting_user, forum=self.forum)
        self.write_new_post(self.forum, other_topic)

        self.read_status.mark(self.topic, self.reading_user)
        self.reading_user.save()

        self.assertFalse(self.read_status(self.forum))

    def test_should_be_false_for_parent_if_child_forum_is_unread(self):
        self.assertFalse(self.read_status(self.parent))

    def test_should_be_true_for_parent_if_marked(self):
        self.read_status.mark(self.parent, self.reading_user)
        self.reading_user.save()

        self.assertTrue(self.read_status(self.parent))

    def test_should_be_true_for_parent_if_child_marked(self):
        self.read_status.mark(self.forum, self.reading_user)
        self.reading_user.save()

        self.assertTrue(self.read_status(self.parent))

    def test_should_be_true_for_parent_if_last_child_topic_marked(self):
        self.read_status.mark(self.topic, self.reading_user)
        self.reading_user.save()

        self.assertTrue(self.read_status(self.parent))

    def test_should_be_false_for_parent_with_unread_topic_if_child_is_marked(self):
        other_topic = Topic.objects.create(title='A test Topic', author=self.posting_user, forum=self.parent)
        self.write_new_post(self.parent, other_topic)

        self.read_status.mark(self.forum, self.reading_user)
        self.reading_user.save()

        self.assertFalse(self.read_status(self.parent))

    def test_should_be_false_for_parent_with_unread_topic_if_child_topic_is_marked(self):
        other_topic = Topic.objects.create(title='A test Topic', author=self.posting_user, forum=self.parent)
        self.write_new_post(self.parent, other_topic)

        self.read_status.mark(self.topic, self.reading_user)
        self.reading_user.save()

        self.assertFalse(self.read_status(self.parent))

    def test_should_be_false_for_parent_with_unread_child_if__other_child_is_marked(self):
        other_child = Forum.objects.create(name='other child', parent=self.parent)
        other_topic = Topic.objects.create(title='A test Topic', author=self.posting_user, forum=other_child)
        self.write_new_post(other_child, other_topic)

        self.read_status.mark(self.forum, self.reading_user)
        self.reading_user.save()

        self.assertFalse(self.read_status(self.parent))

    def test_should_be_false_for_parent_with_unread_child_if_other_child_topic_is_marked(self):
        other_child = Forum.objects.create(name='other child', parent=self.parent)
        other_topic = Topic.objects.create(title='A test Topic', author=self.posting_user, forum=other_child)
        self.write_new_post(other_child, other_topic)

        self.read_status.mark(self.topic, self.reading_user)
        self.reading_user.save()

        self.assertFalse(self.read_status(self.parent))
