from inyoka.forum.models import Forum
from inyoka.portal.user import User
from inyoka.utils.test import TestCase


class TestModelFindWelcome(TestCase):
    def test_anonymous(self):
        """
        Tests that find_welcome returns None, when given with the anonymous user
        even when he accepted it.
        """
        anonymous = User.objects.get_anonymous_user()
        forum = Forum.objects.create(
            name='test forum',
            welcome_title='Message title',
            welcome_text='Message text')
        # Let anonymous accept the text. That should not happend in our views.
        forum.welcome_read_users.add(anonymous)

        self.assertIsNone(forum.find_welcome(anonymous))

    def test_with_message(self):
        user = User.objects.create(username='test_user',email='test_user')
        forum = Forum.objects.create(
            name='test forum',
            welcome_title='Message title',
            welcome_text='Message text')

        self.assertEqual(forum.find_welcome(user), forum)

    def test_with_message_parent(self):
        """
        Test the method on a child forum where the parent has a welcome message.
        """
        user = User.objects.create(username='test_user',email='test_user')
        forum1 = Forum.objects.create(
            name='test forum',
            welcome_title='Message title',
            welcome_text='Message text')
        forum2 = Forum.objects.create(
            name='test forum',
            parent=forum1)

        self.assertEqual(forum2.find_welcome(user), forum1)

    def test_without_message(self):
        """
        Tests the method on a forum without a message.
        """
        user = User.objects.create(username='test_user',email='test_user')
        forum = Forum.objects.create(name='test forum')

        self.assertIsNone(forum.find_welcome(user))

    def test_user_has_accepted(self):
        user = User.objects.create(username='test_user',email='test_user')
        forum = Forum.objects.create(
            name='test forum',
            welcome_title='Message title',
            welcome_text='Message text')
        forum.welcome_read_users.add(user)

        self.assertIsNone(forum.find_welcome(user))

    def test_sub_forum(self):
        """
        Tests a forum, where the child forum has a welcome message but not
        the parent forum.
        """
        user = User.objects.create(username='test_user',email='test_user')
        forum = Forum.objects.create(
            name='test forum')
        sub_forum = Forum.objects.create(
            name='test forum',
            parent=forum,
            welcome_title='Message title',
            welcome_text='Message text')

        self.assertEqual(sub_forum.find_welcome(user), sub_forum)

    def test_sub_forum_and_parent(self):
        """
        Tests a forum, where the child forum and the parent have welcome
        messages.
        """
        user = User.objects.create(username='test_user',email='test_user')
        forum = Forum.objects.create(
            name='test forum',
            welcome_title='Message title',
            welcome_text='Message text')
        sub_forum = Forum.objects.create(
            name='test forum',
            parent=forum,
            welcome_title='Message title',
            welcome_text='Message text')

        self.assertEqual(sub_forum.find_welcome(user), forum)

    def test_sub_forum_and_parent_accepted_sub_forum(self):
        """
        Tests a forum, where the child forum and the parent have welcome
        messages.

        The user has accepted the sub forum
        """
        user = User.objects.create(username='test_user',email='test_user')
        forum = Forum.objects.create(
            name='test forum',
            welcome_title='Message title',
            welcome_text='Message text')
        sub_forum = Forum.objects.create(
            name='test forum',
            parent=forum,
            welcome_title='Message title',
            welcome_text='Message text')
        sub_forum.welcome_read_users.add(user)

        self.assertEqual(sub_forum.find_welcome(user), forum)

    def test_sub_forum_and_parent_accepted_parent(self):
        """
        Tests a forum, where the child forum and the parent have welcome
        messages.

        The user has accepted the parent forum
        """
        user = User.objects.create(username='test_user',email='test_user')
        forum = Forum.objects.create(
            name='test forum',
            welcome_title='Message title',
            welcome_text='Message text')
        sub_forum = Forum.objects.create(
            name='test forum',
            parent=forum,
            welcome_title='Message title',
            welcome_text='Message text')
        forum.welcome_read_users.add(user)

        self.assertEqual(sub_forum.find_welcome(user), sub_forum)


class TestModelReadWelcome(TestCase):
    def test_on_anonymous(self):
        """
        Test that forum.read_welcome does nothing for anonymous users.
        """
        anonymous = User.objects.get_anonymous_user()
        forum = Forum.objects.create(
            name='test forum',
            welcome_title='Message title',
            welcome_text='Message text')

        forum.read_welcome(anonymous)

        self.assertFalse(forum.welcome_read_users.filter(pk=anonymous.pk).exists())

    def test_accept(self):
        user = User.objects.create(username='test_user',email='test_user')
        forum = Forum.objects.create(
            name='test forum',
            welcome_title='Message title',
            welcome_text='Message text')

        forum.read_welcome(user)

        self.assertIsNone(forum.find_welcome(user))

    def test_not_accepted(self):
        """
        Tests that a user that accepted the message is "unaccepting" it when
        the read_welcome is called with accepted is False.
        """
        user = User.objects.create(username='test_user',email='test_user')
        forum = Forum.objects.create(
            name='test forum',
            welcome_title='Message title',
            welcome_text='Message text')
        forum.welcome_read_users.add(user)

        forum.read_welcome(user, accepted=False)

        self.assertEqual(forum.find_welcome(user), forum)

    def test_on_forum_without_message(self):
        """
        Tests that read_welcome works also on forums without a message.
        """
        user = User.objects.create(username='test_user',email='test_user')
        forum = Forum.objects.create(name='test forum')

        forum.read_welcome(user)

        self.assertTrue(forum.welcome_read_users.filter(pk=user.pk).exists())
