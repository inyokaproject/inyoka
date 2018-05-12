from inyoka.forum.models import Forum
from inyoka.utils.test import TestCase


class ForumTestCase(TestCase):

    def setUp(self):
        super(ForumTestCase, self).setUp()
        self.parent1 = Forum.objects.create(
            name='This is a test')
        self.parent2 = Forum.objects.create(
            name='This is a second test',
            parent=self.parent1)
        self.forum = Forum.objects.create(
            name='This rocks damnit',
            parent=self.parent2)
