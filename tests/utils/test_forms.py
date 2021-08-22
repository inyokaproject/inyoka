# -*- coding: utf-8 -*-
"""
    tests.utils.test_forms
    ~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2011-2021 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.forms import forms

from inyoka.forum.models import Topic, Forum
from inyoka.portal.user import User
from inyoka.utils.forms import TopicField
from inyoka.utils.test import TestCase


class TestTopicField(TestCase):
    field = TopicField()

    @classmethod
    def setUpClass(cls):
        super(TestTopicField, cls).setUpClass()

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
