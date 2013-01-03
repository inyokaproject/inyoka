#-*- coding: utf-8 -*-
"""
    tests.functional.apps.forum.test_post
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test some forum post related functions.

    :copyright: (c) 2012-2013 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL.
"""
from django.test import TestCase
from django.test.utils import override_settings

from inyoka.forum.models import Forum, Topic, Post
from inyoka.portal.user import User


class TestPostModel(TestCase):

    def setUp(self):
        self.user = User.objects.register_user('admin', 'admin', 'admin', False)

        self.category = Forum(name='category')
        self.category.save()
        self.forum = Forum(name='forum')
        self.forum.save()
        self.topic = Topic(title='topic', author=self.user)
        self.forum.topics.add(self.topic)

    @override_settings(BASE_DOMAIN_NAME='inyoka.local')
    def test_url_for_post(self):
        post = Post(text=u'test1', author=self.user)
        self.topic.posts.add(post)
        self.assertEqual(Post.url_for_post(post.pk),
                         'http://forum.inyoka.local/topic/topic/#post-%s' % post.pk)

    @override_settings(BASE_DOMAIN_NAME='inyoka.local')
    def test_url_for_post_multiple_pages(self):
        posts = []
        for idx in xrange(45):
            post = Post(text=u'test%s' % idx, author=self.user)
            self.topic.posts.add(post)
            posts.append(post.pk)
        self.assertEqual(Post.url_for_post(posts[-1]),
                         'http://forum.inyoka.local/topic/topic/4/#post-%s' % post.pk)

    def test_url_for_post_not_existing_post(self):
        self.assertRaises(Post.DoesNotExist, Post.url_for_post, 250000913)
