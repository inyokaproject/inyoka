"""
    tests.utils.test_forms
    ~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2011-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.forms import forms

from inyoka.forum.models import Forum, Topic
from inyoka.portal.user import User
from inyoka.utils.forms import JabberFormField, TopicField
from inyoka.utils.test import TestCase


class TestTopicField(TestCase):
    field = TopicField()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        topic = Topic.objects.create(slug='valid-slug',
                                     author=User.objects.get_anonymous_user(),
                                     forum=Forum.objects.create(name='This is a test'))
        cls.url = topic.get_absolute_url()
        cls.topic_id = topic.id

    def test_url(self):
        topic = self.field.clean(self.url)
        self.assertEqual(topic.id, self.topic_id)

    def test_slug(self):
        topic = self.field.clean('valid-slug')
        self.assertEqual(topic.id, self.topic_id)

    def test_invalid_slug(self):
        with self.assertRaises(forms.ValidationError):
            self.field.clean('invalid-slug')

    def test_empty_value(self):
        topic = self.field.__class__(required=False).clean('')
        self.assertIsNone(topic)


class TestJabberFormField(TestCase):
    field = JabberFormField()

    def test_valid_jabber_id(self):
        self.field.clean('foo@inyoka.test')

    def test_invalid_jabber_id(self):
        with self.assertRaises(forms.ValidationError):
            self.field.clean('foo')
