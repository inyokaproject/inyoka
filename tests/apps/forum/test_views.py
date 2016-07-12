# -*- coding: utf-8 -*-
"""
    tests.apps.forum.test_views
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test forum views.

    :copyright: (c) 2012-2016 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import shutil
from os import makedirs, path
from random import randint

import responses
from django.conf import settings
from django.core.cache import cache
from django.core.files import File
from django.contrib.auth.models import Group
from django.http import Http404
from django.test import RequestFactory
from django.test.utils import override_settings
from django.utils import translation
from django.utils.translation import ugettext as _
from mock import patch
from guardian.shortcuts import assign_perm, remove_perm

from inyoka.forum import constants, views
from inyoka.forum.models import (
    Attachment,
    Forum,
    Poll,
    PollOption,
    Post,
    Topic,
)
from inyoka.portal.models import Subscription
from inyoka.portal.user import User
from inyoka.utils.test import AntiSpamTestCaseMixin, InyokaClient, TestCase
from inyoka.utils.urls import href, url_for


class TestViews(AntiSpamTestCaseMixin, TestCase):

    client_class = InyokaClient

    def setUp(self):
        super(TestViews, self).setUp()
        self.admin = User.objects.register_user('admin', 'admin@example.com', 'admin', False)
        self.admin.is_superuser = True
        self.admin.save()

        self.user = User.objects.register_user('user', 'user@example.com', 'user', False)
        self.system_user = User.objects.get_system_user()

        self.forum1 = Forum.objects.create(name='Forum 1')
        self.forum2 = Forum.objects.create(name='Forum 2', parent=self.forum1)
        self.forum3 = Forum.objects.create(name='Forum 3', parent=self.forum1)

        self.topic = Topic.objects.create(title='A test Topic', author=self.user,
                forum=self.forum2)
        self.post = Post.objects.create(text=u'Post 1', author=self.user,
                topic=self.topic, position=0)

        self.client.defaults['HTTP_HOST'] = 'forum.%s' % settings.BASE_DOMAIN_NAME
        self.client.login(username='admin', password='admin')

    def tearDown(self):
        from inyoka.portal import user
        user._ANONYMOUS_USER = None
        user._SYSTEM_USER = None

    def _setup_pagination(self):
        """Create enough topics for pagination test"""
        posts = []

        def newtopic():
            t = Topic.objects.create(title="Title %s" % randint(1, 100000),
                                     author=self.user, forum=self.forum3)
            p = Post.objects.create(topic=t, text="Post %s" % randint(1, 100000),
                                    author=self.user, position=0)
            t.first_post_id = p.id
            t.save()
            for i in xrange(1, randint(2, 3)):
                posts.append(Post(
                    text="More Posts %s" % randint(1, 100000), topic=t,
                    author=self.user, position=i,
                ))
            for i in xrange(1, randint(2, 3)):
                posts.append(Post(
                    text="More Posts %s" % randint(1, 100000), topic=t,
                    author=self.admin, position=i,
                ))

        self.num_topics_on_last_page = int(round(constants.TOPICS_PER_PAGE * 0.66))
        for i in xrange(1, 4 * constants.TOPICS_PER_PAGE + self.num_topics_on_last_page):
            newtopic()
        Post.objects.bulk_create(posts)

    def test_reported_topics(self):
        response = self.client.get('/reported_topics/')
        self.assertEqual(response.status_code, 200)

    @patch('inyoka.forum.views.send_notification')
    def test_movetopic(self, mock_send):
        self.assertEqual(Topic.objects.get(id=self.topic.id).forum_id,
                self.forum2.id)
        response = self.client.post('/topic/%s/move/' % self.topic.slug,
                    {'forum': self.forum3.id})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(mock_send.call_count, 1)  # only the topic author
        mock_send.assert_called_with(self.user, 'topic_moved',
            _(u'Your topic “%(topic)s” was moved.') % {'topic': 'A test Topic'}, {
                'username': self.user.username, 'topic': self.topic,
                'mod': self.admin.username, 'forum_name': 'Forum 3',
                'old_forum_name': 'Forum 2'})

        self.assertEqual(Topic.objects.get(id=self.topic.id).forum_id,
                self.forum3.id)

    def test_subscribe(self):
        self.client.login(username='user', password='user')
        registered = Group.objects.get(name=settings.INYOKA_REGISTERED_GROUP_NAME)
        assign_perm('forum.view_forum', registered, self.forum2)

        self.client.get('/topic/%s/subscribe/' % self.topic.slug)
        self.assertTrue(
            Subscription.objects.user_subscribed(self.user, self.topic))

        # Test for unsubscribe-link in the usercp if the user has no more read
        # access to a subscription
        remove_perm('forum.view_forum', registered, self.forum2)
        cache.clear()
        response = self.client.get('/usercp/subscriptions/', {}, False,
                         HTTP_HOST=settings.BASE_DOMAIN_NAME)
        self.assertTrue(
            ('/topic/%s/unsubscribe/?next=' % self.topic.slug)
            in response.content.decode("utf-8")
        )

        forward_url = 'http://%s/myfwd' % settings.BASE_DOMAIN_NAME
        response = self.client.get(
            '/topic/%s/unsubscribe/' % self.topic.slug,
            {'next': forward_url}
        )
        self.assertFalse(
            Subscription.objects.user_subscribed(self.user, self.topic))
        self.assertEqual(response['location'], forward_url)

    def test_continue_admin_index(self):
        """The Parameter continue was renamed into next"""
        response = self.client.get("/", follow=True)
        self.assertEqual(response.status_code, 200)

    def test_continue_admin_forum(self):
        """The Parameter continue was renamed into next"""
        response = self.client.get("/forum/%s/" % self.forum2.slug, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_continue_admin_topic(self):
        """The Parameter continue was renamed into next"""
        response = self.client.get("/topic/%s/" % self.topic.slug, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_continue_user_index(self):
        """The Parameter continue was renamed into next"""
        self.client.logout()
        self.client.login(username='user', password='user')
        response = self.client.get("/", follow=True)
        self.assertEqual(response.status_code, 200)

    def test_continue_user_forum(self):
        """The Parameter continue was renamed into next"""
        self.client.logout()
        self.client.login(username='user', password='user')
        response = self.client.get("/forum/%s/" % self.forum2.slug, follow=True)
        self.assertEqual(response.status_code, 403)

    def test_continue_user_topic(self):
        """The Parameter continue was renamed into next"""
        self.client.logout()
        self.client.login(username='user', password='user')
        response = self.client.get("/topic/%s/" % self.topic.slug, follow=True)
        self.assertEqual(response.status_code, 403)

    @override_settings(PROPAGATE_TEMPLATE_CONTEXT=True)
    @patch('inyoka.forum.views.TOPICS_PER_PAGE', 4)
    @patch('inyoka.forum.constants.TOPICS_PER_PAGE', 4)
    def test_topiclist(self):
        self._setup_pagination()
        self.assertEqual(len(self.client.get("/last24/").tmpl_context['topics']),
                         constants.TOPICS_PER_PAGE)
        self.assertEqual(len(self.client.get("/last24/3/").tmpl_context['topics']),
                         constants.TOPICS_PER_PAGE)
        self.assertEqual(len(self.client.get("/last24/5/").tmpl_context['topics']),
                         self.num_topics_on_last_page)
        self.assertTrue(self.client.get("/last24/6/").status_code == 404)

    def test_service_splittopic(self):
        t1 = Topic.objects.create(title='A: topic', slug='a:-topic',
                author=self.user, forum=self.forum2)
        p1 = Post.objects.create(text=u'Post 1', author=self.user,
                topic=t1)

        t2 = Topic.objects.create(title='Another topic', author=self.user,
                forum=self.forum2)
        p2 = Post.objects.create(text=u'Post 1', author=self.user,
                topic=t2)

        response = self.client.get('/', {
            '__service__': 'forum.mark_topic_split_point',
            'post': p1.pk,
            'topic': 'a%3A-topic'})
        response = self.client.get('/topic/a%3A-topic/split/')
        self.assertEqual(response.status_code, 200)  # was 302 before

        response = self.client.get('/', {
            '__service__': 'forum.mark_topic_split_point',
            'post': p2.pk,
            'topic': t2.slug})
        response = self.client.get('/topic/%s/split/' % t2.slug)
        self.assertEqual(response.status_code, 200)

    def test_splittopic(self):

        def valuelist(topicid, field='id'):
            if isinstance(field, (list, tuple)):
                return list(
                    Post.objects.filter(topic_id=topicid).values_list(*field).order_by('position')
                )
            else:
                return list(
                    Post.objects.filter(topic_id=topicid).values_list(field, flat=True).order_by('position')
                )

        t1 = Topic.objects.create(title='Topic 1', slug='topic-1',
                author=self.user, forum=self.forum2)
        p11 = Post.objects.create(text=u'Post 1-1', author=self.user,
                topic=t1, position=0)
        p12 = Post.objects.create(text=u'Post 1-2', author=self.user,
                topic=t1)
        p13 = Post.objects.create(text=u'Post 1-3', author=self.user,
                topic=t1)

        t2 = Topic.objects.create(title='Topic 2', slug='topic-2',
                author=self.user, forum=self.forum2)
        p21 = Post.objects.create(text=u'Post 2-1', author=self.user,
                topic=t2, position=0)
        p22 = Post.objects.create(text=u'Post 2-2', author=self.user,
                topic=t2)
        p23 = Post.objects.create(text=u'Post 2-3', author=self.user,
                topic=t2)

        self.client.get('/', {
            '__service__': 'forum.mark_topic_split_point',
            'post': p12.pk,
            'from_here': 'true',
            'topic': t1.slug})
        self.client.post('/topic/%s/split/' % t1.slug, {
            'action': 'add',
            'topic': t2.slug})

        # The order in Topic 2 should now be
        # p21 p22 p23 p12 p13
        self.assertEqual(Post.objects.filter(topic_id=t1.pk).count(), 1)
        self.assertEqual(Post.objects.filter(topic_id=t2.pk).count(), 5)
        self.assertEqual(valuelist(t1.pk), [p11.pk])
        self.assertEqual(valuelist(t2.pk), [p21.pk, p22.pk, p23.pk, p12.pk, p13.pk])
        self.assertEqual(valuelist(t1.pk, 'position'), [0])
        self.assertEqual(valuelist(t2.pk, 'position'), list(xrange(0, 5)))

        # We will now strip all posts beginning at p22 from t2
        self.client.get('/', {
            '__service__': 'forum.mark_topic_split_point',
            'post': p22.pk,
            'from_here': 'true',
            'topic': t2.slug})
        self.client.post('/topic/%s/split/' % t2.slug, {
            'action': 'add',
            'topic': t1.slug})
        # The order in Topic 1 should now be
        # p11 p22 p23 p12 p13
        # Previously is was
        # for Topic 1 p11 p22 p23 and for Topic 2 p21 p12 p13
        self.assertEqual(Post.objects.filter(topic_id=t1.pk).count(), 5)
        self.assertEqual(Post.objects.filter(topic_id=t2.pk).count(), 1)
        self.assertEqual(valuelist(t1.pk), [p11.pk, p22.pk, p23.pk, p12.pk, p13.pk])
        self.assertEqual(valuelist(t2.pk), [p21.pk])
        self.assertEqual(valuelist(t1.pk, 'position'), list(xrange(0, 5)))
        self.assertEqual(valuelist(t2.pk, 'position'), [0])

    @responses.activate
    @override_settings(INYOKA_USE_AKISMET=True)
    def test_topic_mark_ham_admin(self):
        topic = Topic.objects.create(
            title='A test Topic', author=self.user, forum=self.forum2,
            hidden=True, reported='spam', reporter=self.system_user,
        )
        post = Post.objects.create(
            text=u'Post 1', author=self.user, topic=topic, position=0, hidden=False
        )
        self.make_valid_key()
        self.make_mark_ham()
        response = self.client.post('/post/%d/ham/' % post.pk, {'confirm': 'send'})
        self.assertEqual(response.status_code, 302)
        post = Post.objects.select_related('topic').get(pk=post.pk)
        self.assertFalse(post.hidden)
        self.assertFalse(post.topic.hidden)
        # Don't remove the reported marker
        self.assertIn('spam', post.topic.reported)
        self.assertEqual(post.topic.reporter, self.system_user)

    @responses.activate
    @override_settings(INYOKA_USE_AKISMET=True)
    def test_topic_mark_spam_admin(self):
        topic = Topic.objects.create(
            title='A test Topic', author=self.user, forum=self.forum2,
        )
        post = Post.objects.create(
            text=u'Post 1', author=self.user, topic=topic, position=0,
        )
        self.make_valid_key()
        self.make_mark_spam()
        response = self.client.post('/post/%d/spam/' % post.pk, {'confirm': 'send'})
        self.assertEqual(response.status_code, 302)
        post = Post.objects.select_related('topic').get(pk=post.pk)
        self.assertFalse(post.hidden)
        self.assertTrue(post.topic.hidden)
        # Don't mark the topic as reported
        self.assertIsNone(post.topic.reported)
        self.assertIsNone(post.topic.reporter)

    @responses.activate
    @override_settings(INYOKA_USE_AKISMET=True)
    def test_topic_mark_ham_user(self):
        self.client.logout()
        self.client.login(username='user', password='user')

        topic = Topic.objects.create(
            title='A test Topic', author=self.user, forum=self.forum2,
            hidden=True, reported='spam', reporter=self.system_user
        )
        post = Post.objects.create(
            text=u'Post 1', author=self.user, topic=topic, position=0
        )
        self.make_valid_key()
        self.make_mark_ham()
        response = self.client.post('/post/%d/ham/' % post.pk, {'confirm': 'send'})
        self.assertEqual(response.status_code, 403)
        post = Post.objects.select_related('topic__reporter').get(pk=post.pk)
        self.assertFalse(post.hidden)
        self.assertTrue(post.topic.hidden)
        self.assertIn('spam', post.topic.reported)
        self.assertEqual(post.topic.reporter, self.system_user)

    @responses.activate
    @override_settings(INYOKA_USE_AKISMET=True)
    def test_topic_mark_spam_user(self):
        self.client.logout()
        self.client.login(username='user', password='user')

        topic = Topic.objects.create(
            title='A test Topic', author=self.user, forum=self.forum2,
        )
        post = Post.objects.create(
            text=u'Post 1', author=self.user, topic=topic, position=0
        )
        self.make_valid_key()
        self.make_mark_spam()
        response = self.client.post('/post/%d/spam/' % post.pk, {'confirm': 'send'})
        self.assertEqual(response.status_code, 403)
        post = Post.objects.select_related('topic').get(pk=post.pk)
        self.assertFalse(post.hidden)
        self.assertFalse(post.topic.hidden)
        self.assertIsNone(post.topic.reported)
        self.assertIsNone(post.topic.reporter)

    @responses.activate
    @override_settings(INYOKA_USE_AKISMET=True)
    def test_post_mark_ham_admin(self):
        post = Post.objects.create(
            text=u'Post 2', author=self.user, topic=self.topic, position=1, hidden=True
        )
        self.make_valid_key()
        self.make_mark_ham()
        response = self.client.post('/post/%d/ham/' % post.pk, {'confirm': 'send'})
        self.assertEqual(response.status_code, 302)
        post = Post.objects.select_related('topic').get(pk=post.pk)
        self.assertFalse(post.hidden)
        self.assertFalse(post.topic.hidden)

    @responses.activate
    @override_settings(INYOKA_USE_AKISMET=True)
    def test_post_mark_spam_admin(self):
        post = Post.objects.create(
            text=u'Post 2', author=self.user, topic=self.topic, position=1, hidden=False
        )
        self.make_valid_key()
        self.make_mark_spam()
        response = self.client.post('/post/%d/spam/' % post.pk, {'confirm': 'send'})
        self.assertEqual(response.status_code, 302)
        post = Post.objects.select_related('topic').get(pk=post.pk)
        self.assertTrue(post.hidden)
        self.assertFalse(post.topic.hidden)

    @responses.activate
    @override_settings(INYOKA_USE_AKISMET=True)
    def test_post_mark_ham_user(self):
        self.client.logout()
        self.client.login(username='user', password='user')

        post = Post.objects.create(
            text=u'Post 2', author=self.user, topic=self.topic, position=1, hidden=True
        )
        self.make_valid_key()
        self.make_mark_ham()
        response = self.client.post('/post/%d/ham/' % post.pk, {'confirm': 'send'})
        self.assertEqual(response.status_code, 403)
        post = Post.objects.select_related('topic').get(pk=post.pk)
        self.assertTrue(post.hidden)
        self.assertFalse(post.topic.hidden)

    @responses.activate
    @override_settings(INYOKA_USE_AKISMET=True)
    def test_post_mark_spam_user(self):
        self.client.logout()
        self.client.login(username='user', password='user')

        post = Post.objects.create(
            text=u'Post 2', author=self.user, topic=self.topic, position=1, hidden=False
        )
        self.make_valid_key()
        self.make_mark_spam()
        response = self.client.post('/post/%d/spam/' % post.pk, {'confirm': 'send'})
        self.assertEqual(response.status_code, 403)
        post = Post.objects.select_related('topic').get(pk=post.pk)
        self.assertFalse(post.hidden)
        self.assertFalse(post.topic.hidden)


class TestUserPostCounter(TestCase):
    def setUp(self):
        super(TestUserPostCounter, self).setUp()
        self.user = User.objects.register_user('user', 'user@example.com', 'user', False)
        self.user.is_superuser = True
        self.user.save()
        self.client.login(username='user', password='user')
        self.client.defaults['HTTP_HOST'] = 'forum.%s' % settings.BASE_DOMAIN_NAME

        self.forum = Forum.objects.create()

    def test_hide_post(self):
        """
        Tests that the user post counter is decreased, when a post is hidden.
        """
        topic = Topic.objects.create(forum=self.forum, author=self.user)
        Post.objects.create(author=self.user, topic=topic)
        post2 = Post.objects.create(author=self.user, topic=topic)
        cache.set(self.user.post_count.cache_key, 2)

        self.client.post('/post/{}/hide/'.format(post2.id), {'confirm': 'yes'})

        self.assertEqual(self.user.post_count.value(), 1)

    def test_show_post(self):
        """
        Tests that the user post counter is increased, when a post is un hidden.
        """
        topic = Topic.objects.create(forum=self.forum, author=self.user)
        Post.objects.create(author=self.user, topic=topic)
        post2 = Post.objects.create(author=self.user, topic=topic, hidden=True)
        cache.set(self.user.post_count.cache_key, 1)

        self.client.post('/post/{}/restore/'.format(post2.id), {'confirm': 'yes'})

        self.assertEqual(self.user.post_count.value(), 2)

    def test_delete_hidden_post(self):
        """
        Tests that the post counter is not chaned when a hidden post is deleted.
        """
        topic = Topic.objects.create(forum=self.forum, author=self.user)
        Post.objects.create(author=self.user, topic=topic)
        post2 = Post.objects.create(author=self.user, topic=topic, hidden=True)
        cache.set(self.user.post_count.cache_key, 1)

        self.client.post('/post/{}/delete/'.format(post2.id), {'confirm': 'yes'})

        self.assertEqual(self.user.post_count.value(), 1)


class TestPostEditView(AntiSpamTestCaseMixin, TestCase):

    client_class = InyokaClient

    def setUp(self):
        super(TestPostEditView, self).setUp()
        anonymous_group = Group.objects.get(name=settings.INYOKA_ANONYMOUS_GROUP_NAME)
        registered_group = Group.objects.get(name=settings.INYOKA_REGISTERED_GROUP_NAME)
        self.admin = User.objects.register_user('admin', 'admin@example.com', 'admin', False)
        self.admin.is_superuser = True
        self.admin.save()
        self.user = User.objects.register_user('user', 'user@example.com', 'user', False)

        self.category = Forum.objects.create(name='Category')
        self.forum = Forum.objects.create(name='Forum', parent=self.category)

        self.public_category = Forum.objects.create(name='Public category')
        self.public_forum = Forum.objects.create(name='Public forum', parent=self.public_category)

        for privilege in ('forum.view_forum', 'forum.add_topic_forum', 'forum.add_reply_forum'):
            assign_perm(privilege, registered_group, self.category)
            assign_perm(privilege, registered_group, self.forum)
            assign_perm(privilege, registered_group, self.public_category)
            assign_perm(privilege, registered_group, self.public_forum)

        assign_perm('forum.view_forum', anonymous_group, self.public_category)
        assign_perm('forum.view_forum', anonymous_group, self.public_forum)

        self.client.defaults['HTTP_HOST'] = 'forum.%s' % settings.BASE_DOMAIN_NAME

    def tearDown(self):
        from inyoka.portal import user

        self.client.logout()
        for att in Attachment.objects.all():
            att.delete()  # This removes the files too
        PollOption.objects.all().delete()
        Poll.objects.all().delete()

        cache.clear()
        cache.clear()
        user._ANONYMOUS_USER = None

    def post_request(self, path, postdata, topics, posts, attachments=None,
            polls=None, polloptions=None, submit=False):
        if submit:
            if 'preview' in postdata:
                postdata.pop('preview')
            postdata['send'] = True
        else:
            if 'send' in postdata:
                postdata.pop('send')
            postdata['preview'] = True
        with translation.override('en-us'):
            response = self.client.post(path, postdata)
        self.assertEqual(Topic.objects.count(), topics)
        self.assertEqual(Post.objects.count(), posts)
        if attachments:
            self.assertEqual(Attachment.objects.count(), attachments)
        if polls:
            self.assertEqual(Poll.objects.count(), polls)
        if polloptions:
            self.assertEqual(PollOption.objects.count(), polloptions)
        return response

    def assertAttachmentInHTML(self, attachment, response):
        pattern = '<li><a href="%(url)s">%(name)s</a> - %(size)d Bytes<button type="submit" name="delete_attachment" value="%(pk)d">Delete</button></li>'
        self.assertInHTML(pattern % {
            'size': attachment.size,
            'url': attachment.get_absolute_url(),
            'name': attachment.name,
            'pk': attachment.pk
        }, response.content, count=1)

    def assertPreviewInHTML(self, text, response):
        pattern = '<div class="preview_wrapper"><h2 class="title">Preview</h2><div class="preview"><p>%s</p></div></div>'
        self.assertInHTML(pattern % text, response.content, count=1)

    def test_newtopic(self):
        self.client.login(username='admin', password='admin')
        # Test preview
        postdata = {
            'title': 'newpost_title',
            'ubuntu_distro': constants.get_distro_choices()[2][0],
            'text': 'newpost text',
        }
        response = self.post_request('/forum/%s/newtopic/' % self.forum.slug, postdata, 0, 0)
        self.assertPreviewInHTML('newpost text', response)

        # Test send
        self.post_request('/forum/%s/newtopic/' % self.forum.slug, postdata, 1, 1, submit=True)

        # Check that the content is in the database
        self.assertEqual(
            Topic.objects.get(slug='newpost-title').last_post.text,
            'newpost text',
        )

    def test_newtopic_user(self):
        self.client.login(username='user', password='user')
        # Test preview
        postdata = {
            'title': 'newpost_title',
            'ubuntu_distro': constants.get_distro_choices()[2][0],
            'text': 'newpost text',
        }
        response = self.post_request('/forum/%s/newtopic/' % self.forum.slug, postdata, 0, 0)
        self.assertPreviewInHTML('newpost text', response)

        # Test send
        self.post_request('/forum/%s/newtopic/' % self.forum.slug, postdata, 1, 1, submit=True)

        # Check that the content is in the Database
        self.assertEqual(
            Topic.objects.get(slug='newpost-title').last_post.text,
            'newpost text',
        )

    @responses.activate
    @override_settings(INYOKA_USE_AKISMET=True)
    def test_newtopic_user_spam(self):
        self.client.login(username='user', password='user')
        self.make_valid_key()
        self.make_spam()
        # Test preview
        postdata = {
            'title': 'newpost_title',
            'ubuntu_distro': constants.get_distro_choices()[2][0],
            'text': 'newpost text',
        }
        response = self.post_request('/forum/%s/newtopic/' % self.public_forum.slug, postdata, 0, 0)
        self.assertPreviewInHTML('newpost text', response)

        # Test send
        self.post_request('/forum/%s/newtopic/' % self.public_forum.slug, postdata, 1, 1, submit=True)

        # Check for rendered post
        with translation.override('en-us'):
            response = self.client.get('/topic/newpost-title/')
        self.assertInHTML('<div class="message info">Your text is considered spam '
                          'and needs approval from one of the administrators. '
                          'Please be patient, we will get to it as soon as possible. '
                          'You have 4 attempts left before your account will be blocked.</div>',
                          response.content, count=1)
        self.assertInHTML('<div class="error"><p>You do not have permissions to access this page.</p></div>',
                          response.content, count=1)

    @responses.activate
    @override_settings(INYOKA_USE_AKISMET=True)
    def test_newtopic_frequent_user_spam(self):
        # frequent users (>100 posts) should be excluded from spam detection
        cache.set(self.user.post_count.cache_key, 100)
        self.client.login(username='user', password='user')
        self.make_valid_key()
        self.make_spam()
        # Test preview
        postdata = {
            'title': 'newpost_title',
            'ubuntu_distro': constants.get_distro_choices()[2][0],
            'text': 'newpost text',
        }
        response = self.post_request('/forum/%s/newtopic/' % self.public_forum.slug, postdata, 0, 0)
        self.assertPreviewInHTML('newpost text', response)

        # Test send
        self.post_request('/forum/%s/newtopic/' % self.public_forum.slug, postdata, 1, 1, submit=True)

        # Check for rendered post
        with translation.override('en-us'):
            response = self.client.get('/topic/newpost-title/')
        self.assertInHTML('Your text is considered spam', response.content, count=0)

    @responses.activate
    @override_settings(INYOKA_USE_AKISMET=True)
    def test_newtopic_user_spam_non_public(self):
        self.client.login(username='user', password='user')
        self.make_valid_key()
        self.make_spam()
        # Test preview
        postdata = {
            'title': 'newpost_title',
            'ubuntu_distro': constants.get_distro_choices()[2][0],
            'text': 'newpost text',
        }
        response = self.post_request('/forum/%s/newtopic/' % self.forum.slug, postdata, 0, 0)
        self.assertPreviewInHTML('newpost text', response)

        # Test send
        self.post_request('/forum/%s/newtopic/' % self.forum.slug, postdata, 1, 1, submit=True)

        # Check for rendered post
        with translation.override('en-us'):
            response = self.client.get('/topic/newpost-title/')
        self.assertContains(response, 'Your text is considered spam', count=0)

    def test_newtopic_with_file(self):
        TEST_ATTACHMENT = 'test_attachment.png'
        self.client.login(username='admin', password='admin')
        # Test file upload
        f = open(path.join(path.dirname(__file__), TEST_ATTACHMENT), 'rb')
        postdata = {
            'attachment': f,
            'filename': 'newpost_file_name.png',
            'comment': 'newpost file comment',
            'attach': True,
        }
        response = self.post_request('/forum/%s/newtopic/' % self.forum.slug, postdata, 0, 0, attachments=1)
        att = Attachment.objects.get()
        self.assertAttachmentInHTML(att, response)

        # Test preview
        postdata = {
            'title': 'newpost_title',
            'ubuntu_distro': constants.get_distro_choices()[2][0],
            'text': 'newpost text',
            'attachments': str(att.pk),
        }
        response = self.post_request('/forum/%s/newtopic/' % self.forum.slug, postdata, 0, 0, attachments=1)
        self.assertPreviewInHTML('newpost text', response)

        # Test send
        self.post_request('/forum/%s/newtopic/' % self.forum.slug, postdata, 1, 1, attachments=1, submit=True)

        # Check for rendered post
        with translation.override('en-us'):
            response = self.client.get('/topic/newpost-title/')
        self.assertInHTML('<div class="text"><p>newpost text</p></div>', response.content, count=1)
        att = Attachment.objects.get()
        pattern = '<li><a href="%(url)s" type="image/png" title="%(comment)s">Download %(name)s</a></li>'
        self.assertInHTML(pattern % {'url': att.get_absolute_url(), 'comment': att.comment, 'name': att.name}, response.content, count=1)

    def test_newtopic_with_multiple_files(self):
        TEST_ATTACHMENT1 = 'test_attachment.png'
        TEST_ATTACHMENT2 = 'test_attachment2.png'
        self.client.login(username='admin', password='admin')
        # Test file upload #1
        f1 = open(path.join(path.dirname(__file__), TEST_ATTACHMENT1), 'rb')
        postdata = {
            'attachment': f1,
            'filename': 'newpost_file_name.png',
            'comment': 'newpost file comment',
            'attach': True,
        }
        self.post_request('/forum/%s/newtopic/' % self.forum.slug, postdata, 0, 0, attachments=1)
        att1 = Attachment.objects.get()

        # Test file upload #2
        f2 = open(path.join(path.dirname(__file__), TEST_ATTACHMENT2), 'rb')
        postdata = {
            'attachment': f2,
            'filename': 'newpost_second_file.png',
            'comment': 'newpost comment for file 2',
            'attachments': str(att1.pk),
            'attach': True,
        }
        response = self.post_request('/forum/%s/newtopic/' % self.forum.slug, postdata, 0, 0, attachments=2)

        # Verify that the attachments exist
        att1, att2 = Attachment.objects.all()
        self.assertAttachmentInHTML(att1, response)
        self.assertAttachmentInHTML(att2, response)

        # Test preview
        postdata = {
            'title': 'newpost_title',
            'ubuntu_distro': constants.get_distro_choices()[2][0],
            'text': 'newpost text',
            'attachments': '%d,%d' % (att1.pk, att2.pk),
        }
        response = self.post_request('/forum/%s/newtopic/' % self.forum.slug, postdata, 0, 0, attachments=2)
        self.assertPreviewInHTML('newpost text', response)

        # Test send
        self.post_request('/forum/%s/newtopic/' % self.forum.slug, postdata, 1, 1, attachments=2, submit=True)

        # Check for rendered post
        with translation.override('en-us'):
            response = self.client.get('/topic/newpost-title/')
        self.assertInHTML('<div class="text"><p>newpost text</p></div>', response.content, count=1)
        att1, att2 = Attachment.objects.all()
        pattern = '<li><a href="%(url)s" type="image/png" title="%(comment)s">Download %(name)s</a></li>'
        self.assertInHTML(pattern % {'url': att1.get_absolute_url(), 'comment': att1.comment, 'name': att1.name}, response.content, count=1)
        self.assertInHTML(pattern % {'url': att2.get_absolute_url(), 'comment': att2.comment, 'name': att2.name}, response.content, count=1)

    def test_newtopic_with_poll(self):
        self.client.login(username='admin', password='admin')
        # Add first poll
        postdata = {
            'question': "What shall I ask?",
            'options': ['this', 'that'],
            'add_poll': True,
        }
        response = self.post_request('/forum/%s/newtopic/' % self.forum.slug, postdata, 0, 0, polls=1, polloptions=2)
        poll = Poll.objects.get()
        pattern = '<li>%(q)s<button name="delete_poll" value="%(pk)d">Delete</button></li>'
        self.assertInHTML(pattern % {'q': poll.question, 'pk': poll.pk}, response.content, count=1)

        # Test preview
        postdata = {
            'title': 'newpost_title',
            'ubuntu_distro': constants.get_distro_choices()[2][0],
            'text': 'newpost text',
            'polls': str(poll.pk),
        }
        response = self.post_request('/forum/%s/newtopic/' % self.forum.slug, postdata, 0, 0, polls=1, polloptions=2)
        self.assertPreviewInHTML('newpost text', response)

        # Test send
        self.post_request('/forum/%s/newtopic/' % self.forum.slug, postdata, 1, 1, polls=1, polloptions=2, submit=True)

        # Check for rendered post
        with translation.override('en-us'):
            response = self.client.get('/topic/newpost-title/')
        self.assertInHTML('<div class="text"><p>newpost text</p></div>', response.content, count=1)
        poll = Poll.objects.get()
        opt1, opt2 = PollOption.objects.all()
        pattern = '<tr><td><input type="radio" name="poll_%(poll_pk)d" id="option_%(opt_pk)d" value="%(opt_pk)d"/><label for="option_%(opt_pk)d">%(opt)s</label></td></tr>'
        self.assertInHTML('<div><strong>%(question)s</strong></div>' % {'question': poll.question}, response.content, count=1)
        self.assertInHTML(pattern % {'poll_pk': poll.pk, 'opt': opt1.name, 'opt_pk': opt1.pk}, response.content, count=1)
        self.assertInHTML(pattern % {'poll_pk': poll.pk, 'opt': opt2.name, 'opt_pk': opt2.pk}, response.content, count=1)

    def test_newtopic_with_multiple_polls(self):
        self.client.login(username='admin', password='admin')
        # Test add poll #1
        postdata = {
            'question': "What shall I ask?",
            'options': ['this', 'that'],
            'add_poll': True,
        }
        self.post_request('/forum/%s/newtopic/' % self.forum.slug, postdata, 0, 0, polls=1, polloptions=2)
        poll1 = Poll.objects.get()

        # Test add poll #2
        postdata = {
            'question': "Ask something else!",
            'options': ['Lorem', 'Ipsum'],
            'add_poll': True,
            'polls': str(poll1.pk),
        }
        response = self.post_request('/forum/%s/newtopic/' % self.forum.slug, postdata, 0, 0, polls=2, polloptions=4)

        # Verify that the polls exist
        poll1, poll2 = Poll.objects.all()
        pattern = '<li>%(q)s<button name="delete_poll" value="%(pk)d">Delete</button></li>'
        self.assertInHTML(pattern % {'q': poll1.question, 'pk': poll1.pk}, response.content, count=1)
        self.assertInHTML(pattern % {'q': poll2.question, 'pk': poll2.pk}, response.content, count=1)

        # Test preview
        postdata = {
            'title': 'newpost_title',
            'ubuntu_distro': constants.get_distro_choices()[2][0],
            'text': 'newpost text',
            'polls': '%d,%d' % (poll1.pk, poll2.pk),
        }
        response = self.post_request('/forum/%s/newtopic/' % self.forum.slug, postdata, 0, 0, polls=2, polloptions=4)
        self.assertPreviewInHTML('newpost text', response)

        # Test send
        # The assert calls are inside the function self.post_request()
        self.post_request('/forum/%s/newtopic/' % self.forum.slug, postdata, 1, 1, polls=2, polloptions=4, submit=True)

    def test_new_post(self):
        topic = Topic.objects.create(title='topic', author=self.admin, forum=self.forum)
        Post.objects.create(text=u'first post', author=self.admin, position=0, topic=topic)

        self.client.login(username='admin', password='admin')
        # Test preview
        postdata = {
            'text': 'newpost text',
        }
        response = self.post_request('/topic/%s/reply/' % topic.slug, postdata, 1, 1)
        self.assertPreviewInHTML('newpost text', response)

        # Test send
        self.post_request('/topic/%s/reply/' % topic.slug, postdata, 1, 2, submit=True)

        # Test that the data is in the database
        self.assertEqual(
            Topic.objects.get(pk=topic.pk).last_post.text,
            'newpost text',
        )

    def test_new_post_user(self):
        topic = Topic.objects.create(title='topic', author=self.admin, forum=self.forum)
        Post.objects.create(text=u'first post', author=self.admin, position=0, topic=topic)

        self.client.login(username='user', password='user')
        # Test preview
        postdata = {
            'text': 'newpost text',
        }
        response = self.post_request('/topic/%s/reply/' % topic.slug, postdata, 1, 1)
        self.assertPreviewInHTML('newpost text', response)

        # Test send
        self.post_request('/topic/%s/reply/' % topic.slug, postdata, 1, 2, submit=True)

        # Test that the data is in the database
        self.assertEqual(
            Topic.objects.get(pk=topic.pk).last_post.text,
            'newpost text',
        )

    @responses.activate
    @override_settings(INYOKA_USE_AKISMET=True)
    def test_new_post_user_spam(self):
        topic = Topic.objects.create(title='topic', author=self.admin, forum=self.public_forum)
        Post.objects.create(text=u'first post', author=self.admin, position=0, topic=topic)

        self.client.login(username='user', password='user')
        self.make_valid_key()
        self.make_spam()
        # Test preview
        postdata = {
            'text': 'newpost text',
        }
        response = self.post_request('/topic/%s/reply/' % topic.slug, postdata, 1, 1)
        self.assertPreviewInHTML('newpost text', response)

        # Test send
        self.post_request('/topic/%s/reply/' % topic.slug, postdata, 1, 2, submit=True)

        # Check for rendered post
        with translation.override('en-us'):
            response = self.client.get('/topic/%s/' % topic.slug)
        self.assertInHTML('<div class="message info">Your text is considered spam '
                          'and needs approval from one of the administrators. '
                          'Please be patient, we will get to it as soon as possible. '
                          'You have 4 attempts left before your account will be blocked.</div>',
                          response.content, count=1)
        self.assertInHTML('<div class="text"><p>newpost text</p></div>', response.content, count=1)

    @responses.activate
    @override_settings(INYOKA_USE_AKISMET=True)
    def test_new_post_frequent_user_spam(self):
        # frequent users (>100 posts) should be excluded from spam detection
        cache.set(self.user.post_count.cache_key, 100)
        topic = Topic.objects.create(title='topic', author=self.admin, forum=self.public_forum)
        Post.objects.create(text=u'first post', author=self.admin, position=0, topic=topic)

        self.client.login(username='user', password='user')
        self.make_valid_key()
        self.make_spam()
        # Test preview
        postdata = {
            'text': 'newpost text',
        }
        response = self.post_request('/topic/%s/reply/' % topic.slug, postdata, 1, 1)
        self.assertPreviewInHTML('newpost text', response)

        # Test send
        self.post_request('/topic/%s/reply/' % topic.slug, postdata, 1, 2, submit=True)

        # Check for rendered post
        with translation.override('en-us'):
            response = self.client.get('/topic/%s/' % topic.slug)
        self.assertInHTML('Your text is considered spam', response.content, count=0)

    @responses.activate
    @override_settings(INYOKA_USE_AKISMET=True)
    def test_new_post_user_spam_non_public(self):
        topic = Topic.objects.create(title='topic', author=self.admin, forum=self.forum)
        Post.objects.create(text=u'first post', author=self.admin, position=0, topic=topic)

        self.client.login(username='user', password='user')
        self.make_valid_key()
        self.make_spam()
        # Test preview
        postdata = {
            'text': 'newpost text',
        }
        response = self.post_request('/topic/%s/reply/' % topic.slug, postdata, 1, 1)
        self.assertPreviewInHTML('newpost text', response)

        # Test send
        self.post_request('/topic/%s/reply/' % topic.slug, postdata, 1, 2, submit=True)

        # Check for rendered post
        with translation.override('en-us'):
            response = self.client.get('/topic/%s/' % topic.slug)
        self.assertContains(response, 'Your text is considered spam', count=0)
        self.assertInHTML('<div class="text"><p>newpost text</p></div>', response.content, count=1)

    def test_new_post_with_file(self):
        topic = Topic.objects.create(title='topic', author=self.admin, forum=self.forum)
        Post.objects.create(text=u'first post', author=self.admin, position=0, topic=topic)

        TEST_ATTACHMENT = 'test_attachment.png'
        self.client.login(username='admin', password='admin')
        # Test file upload
        f = open(path.join(path.dirname(__file__), TEST_ATTACHMENT), 'rb')
        postdata = {
            'attachment': f,
            'filename': 'newpost_file_name.png',
            'comment': 'newpost file comment',
            'attach': True,
        }
        response = self.post_request('/topic/%s/reply/' % topic.slug, postdata, 1, 1, attachments=1)
        att = Attachment.objects.get()
        self.assertAttachmentInHTML(att, response)

        # Test preview
        postdata = {
            'text': 'newpost text',
            'attachments': str(att.pk),
        }
        response = self.post_request('/topic/%s/reply/' % topic.slug, postdata, 1, 1, attachments=1)
        self.assertPreviewInHTML('newpost text', response)

        # Test send
        self.post_request('/topic/%s/reply/' % topic.slug, postdata, 1, 2, attachments=1, submit=True)

        # Check for rendered post
        with translation.override('en-us'):
            response = self.client.get('/topic/%s/' % topic.slug)
        self.assertInHTML('<div class="text"><p>newpost text</p></div>', response.content, count=1)
        att = Attachment.objects.get()
        pattern = '<li><a href="%(url)s" type="image/png" title="%(comment)s">Download %(name)s</a></li>'
        self.assertInHTML(pattern % {'url': att.get_absolute_url(), 'comment': att.comment, 'name': att.name}, response.content, count=1)

    def test_new_post_with_multiple_files(self):
        topic = Topic.objects.create(title='topic', author=self.admin, forum=self.forum)
        Post.objects.create(text=u'first post', author=self.admin, position=0, topic=topic)

        TEST_ATTACHMENT1 = 'test_attachment.png'
        TEST_ATTACHMENT2 = 'test_attachment2.png'
        self.client.login(username='admin', password='admin')
        # Test file upload #1
        f1 = open(path.join(path.dirname(__file__), TEST_ATTACHMENT1), 'rb')
        postdata = {
            'attachment': f1,
            'filename': 'newpost_file_name.png',
            'comment': 'newpost file comment',
            'attach': True,
        }
        self.post_request('/topic/%s/reply/' % topic.slug, postdata, 1, 1, attachments=1)
        att1 = Attachment.objects.get()

        # Test file upload #2
        f2 = open(path.join(path.dirname(__file__), TEST_ATTACHMENT2), 'rb')
        postdata = {
            'attachment': f2,
            'filename': 'newpost_second_file.png',
            'comment': 'newpost comment for file 2',
            'attachments': str(att1.pk),
            'attach': True,
        }
        response = self.post_request('/topic/%s/reply/' % topic.slug, postdata, 1, 1, attachments=2)

        # Verify that the attachments exist
        att1, att2 = Attachment.objects.all()
        self.assertAttachmentInHTML(att1, response)
        self.assertAttachmentInHTML(att2, response)

        # Test preview
        postdata = {
            'text': 'newpost text',
            'attachments': '%d,%d' % (att1.pk, att2.pk),
        }
        response = self.post_request('/topic/%s/reply/' % topic.slug, postdata, 1, 1, attachments=2)
        self.assertPreviewInHTML('newpost text', response)

        # Test send
        self.post_request('/topic/%s/reply/' % topic.slug, postdata, 1, 2, attachments=2, submit=True)

        # Check for rendered post
        with translation.override('en-us'):
            response = self.client.get('/topic/%s/' % topic.slug)
        self.assertInHTML('<div class="text"><p>newpost text</p></div>', response.content, count=1)
        att1, att2 = Attachment.objects.all()
        pattern = '<li><a href="%(url)s" type="image/png" title="%(comment)s">Download %(name)s</a></li>'
        self.assertInHTML(pattern % {'url': att1.get_absolute_url(), 'comment': att1.comment, 'name': att1.name}, response.content, count=1)
        self.assertInHTML(pattern % {'url': att2.get_absolute_url(), 'comment': att2.comment, 'name': att2.name}, response.content, count=1)

    def test_edit_post(self):
        topic = Topic.objects.create(title='topic', author=self.admin, forum=self.forum)
        Post.objects.create(text=u'first post', author=self.admin, position=0, topic=topic)
        post = Post.objects.create(text=u'second post', author=self.admin, position=1, topic=topic)

        self.client.login(username='admin', password='admin')
        # Test preview
        postdata = {
            'text': 'editpost text',
        }
        response = self.post_request('/post/%d/edit/' % post.pk, postdata, 1, 2)
        self.assertPreviewInHTML('editpost text', response)

        # Test send
        self.post_request('/post/%d/edit/' % post.pk, postdata, 1, 2, submit=True)

        # Check for rendered post
        with translation.override('en-us'):
            response = self.client.get('/topic/%s/' % topic.slug)
        self.assertInHTML('<div class="text"><p>editpost text</p></div>', response.content, count=1)

    def test_edit_post_user(self):
        topic = Topic.objects.create(title='topic', author=self.admin, forum=self.forum)
        Post.objects.create(text=u'first post', author=self.admin, position=0, topic=topic)
        post = Post.objects.create(text=u'second post', author=self.user, position=1, topic=topic)

        self.client.login(username='user', password='user')
        # Test preview
        postdata = {
            'text': 'editpost text',
        }
        response = self.post_request('/post/%d/edit/' % post.pk, postdata, 1, 2)
        self.assertPreviewInHTML('editpost text', response)

        # Test send
        self.post_request('/post/%d/edit/' % post.pk, postdata, 1, 2, submit=True)

        # Check for rendered post
        with translation.override('en-us'):
            response = self.client.get('/topic/%s/' % topic.slug)
        self.assertInHTML('<div class="text"><p>editpost text</p></div>', response.content, count=1)

    @responses.activate
    @override_settings(INYOKA_USE_AKISMET=True)
    def test_edit_post_user_spam(self):
        # Edited posts are never considered spam, not even from users
        topic = Topic.objects.create(title='topic', author=self.admin, forum=self.public_forum)
        Post.objects.create(text=u'first post', author=self.admin, position=0, topic=topic)
        post = Post.objects.create(text=u'second post', author=self.user, position=1, topic=topic)

        self.client.login(username='user', password='user')
        self.make_valid_key()
        self.make_spam()
        # Test preview
        postdata = {
            'text': 'editpost text',
        }
        response = self.post_request('/post/%d/edit/' % post.pk, postdata, 1, 2)
        self.assertPreviewInHTML('editpost text', response)

        # Test send
        self.post_request('/post/%d/edit/' % post.pk, postdata, 1, 2, submit=True)

        # Check for rendered post
        with translation.override('en-us'):
            response = self.client.get('/topic/%s/' % topic.slug)
        self.assertInHTML('<div class="text"><p>editpost text</p></div>', response.content, count=1)

    @responses.activate
    @override_settings(INYOKA_USE_AKISMET=True)
    def test_edit_post_user_spam_non_public(self):
        topic = Topic.objects.create(title='topic', author=self.admin, forum=self.forum)
        Post.objects.create(text=u'first post', author=self.admin, position=0, topic=topic)
        post = Post.objects.create(text=u'second post', author=self.user, position=1, topic=topic)

        self.client.login(username='user', password='user')
        self.make_valid_key()
        self.make_spam()
        # Test preview
        postdata = {
            'text': 'editpost text',
        }
        response = self.post_request('/post/%d/edit/' % post.pk, postdata, 1, 2)
        self.assertPreviewInHTML('editpost text', response)

        # Test send
        self.post_request('/post/%d/edit/' % post.pk, postdata, 1, 2, submit=True)

        # Check for rendered post
        with translation.override('en-us'):
            response = self.client.get('/topic/%s/' % topic.slug)
        self.assertContains(response, 'Your text is considered spam', count=0)
        self.assertInHTML('<div class="text"><p>editpost text</p></div>', response.content, count=1)

    def test_edit_post_remove_attachments(self):
        TEST_ATTACHMENT1 = 'test_attachment.png'
        TEST_ATTACHMENT2 = 'test_attachment2.png'
        self.client.login(username='admin', password='admin')

        topic = Topic.objects.create(title='topic', author=self.admin, forum=self.forum)
        Post.objects.create(text=u'first post', author=self.admin, position=0, topic=topic)
        post = Post.objects.create(text=u'second post', author=self.admin, position=1, topic=topic)

        basedir = path.join(settings.MEDIA_ROOT, 'forum', 'attachments', '00', '00')
        if not path.exists(basedir):
            makedirs(basedir)
        new_file1 = path.join(basedir, TEST_ATTACHMENT1)
        shutil.copy(path.join(path.dirname(__file__), TEST_ATTACHMENT1), new_file1)
        new_file2 = path.join(basedir, TEST_ATTACHMENT2)
        shutil.copy(path.join(path.dirname(__file__), TEST_ATTACHMENT2), new_file2)

        with open(new_file1, 'rb') as f:
            att1 = Attachment.objects.create(name=TEST_ATTACHMENT1, file=File(f), mimetype='image/png', post=post)
        with open(new_file2, 'rb') as f:
            att2 = Attachment.objects.create(name=TEST_ATTACHMENT2, file=File(f), mimetype='image/png', post=post)
        # FIXME: Move this stuff to the model!
        post.has_attachments = True
        post.save(update_fields=['has_attachments'])

        # Test existing data
        with translation.override('en-us'):
            response = self.client.get('/post/%d/edit/' % post.pk)
        self.assertEqual(Topic.objects.count(), 1)
        self.assertEqual(Post.objects.count(), 2)
        self.assertEqual(Attachment.objects.count(), 2)
        self.assertAttachmentInHTML(att1, response)
        self.assertAttachmentInHTML(att2, response)

        # Test attachment deletion 1
        postdata = {
            'delete_attachment': str(att1.pk),
            'attachments': '%d,%d' % (att1.pk, att2.pk),
            'text': 'edit 1',
        }

        with translation.override('en-us'):
            response = self.client.post('/post/%d/edit/' % post.pk, postdata)
        self.assertEqual(Topic.objects.count(), 1)
        self.assertEqual(Post.objects.count(), 2)
        self.assertEqual(Attachment.objects.count(), 1)
        self.assertTrue(Post.objects.get(pk=post.pk).has_attachments)
        self.assertInHTML('<textarea id="id_text" rows="10" cols="40" name="text">edit 1</textarea>', response.content)
        self.assertAttachmentInHTML(att2, response)

        # Test attachment deletion 2
        postdata = {
            'delete_attachment': str(att2.pk),
            'attachments': att2.pk,
            'text': 'edit 2',
        }

        with translation.override('en-us'):
            response = self.client.post('/post/%d/edit/' % post.pk, postdata)
        self.assertEqual(Topic.objects.count(), 1)
        self.assertEqual(Post.objects.count(), 2)
        self.assertEqual(Attachment.objects.count(), 0)
        self.assertTrue(Post.objects.get(pk=post.pk).has_attachments)
        self.assertInHTML('<textarea id="id_text" rows="10" cols="40" name="text">edit 2</textarea>', response.content)

        postdata = {
            'text': 'edit 3',
        }
        response = self.post_request('/post/%d/edit/' % post.pk, postdata, 1, 2)
        self.assertPreviewInHTML('edit 3', response)
        self.assertTrue(Post.objects.get(pk=post.pk).has_attachments)

        # We must submit the entire form since deleting an attachment does not update the has_attachments information
        self.post_request('/post/%d/edit/' % post.pk, postdata, 1, 2, submit=True)
        self.assertFalse(Post.objects.get(pk=post.pk).has_attachments)

        # Check for rendered post
        with translation.override('en-us'):
            response = self.client.get('/topic/%s/' % topic.slug)
        self.assertInHTML('<div class="text"><p>edit 3</p></div>', response.content, count=1)

    def test_edit_first_post(self):
        topic = Topic.objects.create(title='topic', author=self.admin, forum=self.forum)
        post = Post.objects.create(text=u'first post', author=self.admin, position=0, topic=topic)

        self.client.login(username='admin', password='admin')
        # Test preview
        postdata = {
            'title': 'edited title',
            'text': 'edited text',
        }
        response = self.post_request('/post/%d/edit/' % post.pk, postdata, 1, 1)
        self.assertInHTML('<input id="id_title" name="title" size="60" type="text" value="edited title">', response.content)
        self.assertPreviewInHTML('edited text', response)

        # Test send
        self.post_request('/post/%d/edit/' % post.pk, postdata, 1, 1, submit=True)

        # Check for rendered post
        with translation.override('en-us'):
            response = self.client.get('/topic/%s/' % topic.slug)
        self.assertInHTML('<h2>edited title</h2>', response.content, count=1)
        self.assertInHTML('<div class="text"><p>edited text</p></div>', response.content, count=1)

    def test_edit_first_post_user(self):
        topic = Topic.objects.create(title='topic', author=self.user, forum=self.forum)
        post = Post.objects.create(text=u'first post', author=self.user, position=0, topic=topic)

        self.client.login(username='user', password='user')
        # Test preview
        postdata = {
            'title': 'edited title',
            'text': 'edited text',
        }
        response = self.post_request('/post/%d/edit/' % post.pk, postdata, 1, 1)
        self.assertInHTML('<input id="id_title" name="title" size="60" type="text" value="edited title">', response.content)
        self.assertPreviewInHTML('edited text', response)

        # Test send
        self.post_request('/post/%d/edit/' % post.pk, postdata, 1, 1, submit=True)

        # Check for rendered post
        with translation.override('en-us'):
            response = self.client.get('/topic/%s/' % topic.slug)
        self.assertInHTML('<h2>edited title</h2>', response.content, count=1)
        self.assertInHTML('<div class="text"><p>edited text</p></div>', response.content, count=1)

    @responses.activate
    @override_settings(INYOKA_USE_AKISMET=True)
    def test_edit_first_post_user_spam(self):
        # Edited posts are never considered spam, not even from users
        topic = Topic.objects.create(title='topic', author=self.user, forum=self.public_forum)
        post = Post.objects.create(text=u'first post', author=self.user, position=0, topic=topic)

        self.client.login(username='user', password='user')
        self.make_valid_key()
        self.make_spam()
        # Test preview
        postdata = {
            'title': 'edited title',
            'text': 'edited text',
        }
        response = self.post_request('/post/%d/edit/' % post.pk, postdata, 1, 1)
        self.assertInHTML('<input id="id_title" name="title" size="60" type="text" value="edited title">', response.content)
        self.assertPreviewInHTML('edited text', response)

        # Test send
        self.post_request('/post/%d/edit/' % post.pk, postdata, 1, 1, submit=True)

        # Check for rendered post
        with translation.override('en-us'):
            response = self.client.get('/topic/%s/' % topic.slug)
        self.assertInHTML('<h2>edited title</h2>', response.content, count=1)
        self.assertInHTML('<div class="text"><p>edited text</p></div>', response.content, count=1)

    @responses.activate
    @override_settings(INYOKA_USE_AKISMET=True)
    def test_edit_first_post_user_spam_non_public(self):
        topic = Topic.objects.create(title='topic', author=self.user, forum=self.forum)
        post = Post.objects.create(text=u'first post', author=self.user, position=0, topic=topic)

        self.client.login(username='user', password='user')
        self.make_valid_key()
        self.make_spam()
        # Test preview
        postdata = {
            'title': 'edited title',
            'text': 'edited text',
        }
        response = self.post_request('/post/%d/edit/' % post.pk, postdata, 1, 1)
        self.assertInHTML('<input id="id_title" name="title" size="60" type="text" value="edited title">', response.content)
        self.assertPreviewInHTML('edited text', response)

        # Test send
        self.post_request('/post/%d/edit/' % post.pk, postdata, 1, 1, submit=True)

        # Check for rendered post
        with translation.override('en-us'):
            response = self.client.get('/topic/%s/' % topic.slug)
        self.assertContains(response, 'Your text is considered spam', count=0)
        self.assertInHTML('<div class="text"><p>edited text</p></div>', response.content, count=1)

    def test_edit_first_post_remove_polls(self):
        topic = Topic.objects.create(title='topic', author=self.admin, forum=self.forum)
        post = Post.objects.create(text=u'first post', author=self.admin, position=0, topic=topic)
        poll1 = Poll.objects.create(question='some first question', topic=topic)
        poll2 = Poll.objects.create(question='some second question', topic=topic)
        PollOption.objects.create(poll=poll1, name='option11')
        PollOption.objects.create(poll=poll1, name='option12')
        PollOption.objects.create(poll=poll2, name='option21')
        PollOption.objects.create(poll=poll2, name='option22')

        self.client.login(username='admin', password='admin')
        with translation.override('en-us'):
            response = self.client.get('/post/%d/edit/' % post.pk)
        pattern = '<li>%(q)s<button name="delete_poll" value="%(pk)d">Delete</button></li>'
        self.assertInHTML(pattern % {'q': poll1.question, 'pk': poll1.pk}, response.content, count=1)
        self.assertInHTML(pattern % {'q': poll2.question, 'pk': poll2.pk}, response.content, count=1)

        postdata = {
            'title': 'edited title',
            'text': 'edited text',
            'polls': '%d,%d' % (poll1.pk, poll2.pk),
            'delete_poll': str(poll1.pk),
        }
        with translation.override('en-us'):
            response = self.client.post('/post/%d/edit/' % post.pk, postdata)
        self.assertEqual(Topic.objects.count(), 1)
        self.assertEqual(Post.objects.count(), 1)
        self.assertEqual(Poll.objects.count(), 1)
        self.assertEqual(PollOption.objects.count(), 2)
        pattern = '<li>%(q)s<button name="delete_poll" value="%(pk)d">Delete</button></li>'
        self.assertInHTML(pattern % {'q': poll2.question, 'pk': poll2.pk}, response.content, count=1)
        self.assertInHTML('<input id="id_title" name="title" size="60" type="text" value="edited title">', response.content)

        postdata = {
            'title': 'edited title 2',
            'text': 'edited text 2',
            'polls': str(poll2.pk),
            'delete_poll': str(poll2.pk),
        }
        with translation.override('en-us'):
            response = self.client.post('/post/%d/edit/' % post.pk, postdata)
        self.assertEqual(Topic.objects.count(), 1)
        self.assertEqual(Post.objects.count(), 1)
        self.assertEqual(Poll.objects.count(), 0)
        self.assertEqual(PollOption.objects.count(), 0)
        self.assertInHTML('<input id="id_title" name="title" size="60" type="text" value="edited title 2">', response.content)

        postdata = {
            'title': 'edited title 3',
            'text': 'edited text 3',
        }
        # Test send
        response = self.post_request('/post/%d/edit/' % post.pk, postdata, 1, 1)
        self.assertPreviewInHTML('edited text 3', response)

        postdata = {
            'title': 'edited title 4',
            'text': 'edited text 4',
        }
        # Test send
        self.post_request('/post/%d/edit/' % post.pk, postdata, 1, 1, submit=True)

        # Check for rendered post
        with translation.override('en-us'):
            response = self.client.get('/topic/%s/' % topic.slug)
        self.assertInHTML('<h2>edited title 4</h2>', response.content, count=1)
        self.assertInHTML('<div class="text"><p>edited text 4</p></div>', response.content, count=1)


class TestWelcomeMessageView(TestCase):
    def test_post_accept(self):
        user = User.objects.create(username='testuser',email='testuser')
        forum = Forum.objects.create(slug='f-slug', welcome_title='test')
        request = RequestFactory().post('/fake/', {'accept': True})
        request.user = user

        with patch.object(views.WelcomeMessageView, 'has_permission') as mock_has_permission:
            mock_has_permission.return_value = True
            response = views.WelcomeMessageView.as_view()(request, slug='f-slug')

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], url_for(forum))
        self.assertTrue(forum.welcome_read_users.filter(pk=user.pk).exists())

    def test_post_not_deny(self):
        user = User.objects.create(username='testuser',email='testuser')
        forum = Forum.objects.create(slug='f-slug', welcome_title='test')
        request = RequestFactory().post('/fake/', {})
        request.user = user

        with patch.object(views.WelcomeMessageView, 'has_permission') as mock_has_permission:
            mock_has_permission.return_value = True
            response = views.WelcomeMessageView.as_view()(request, slug='f-slug')

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], href('forum'))
        self.assertFalse(forum.welcome_read_users.filter(pk=user.pk).exists())

    def test_forum_has_no_welcome_message(self):
        user = User.objects.create(username='testuser',email='testuser')
        forum = Forum.objects.create(slug='f-slug')
        request = RequestFactory().get('/fake/')
        request.user = user

        with patch.object(views.WelcomeMessageView, 'has_permission') as mock_has_permission:
            mock_has_permission.return_value = True
            with self.assertRaises(Http404):
                views.WelcomeMessageView.as_view()(request, slug='f-slug')

        self.assertFalse(forum.welcome_read_users.filter(pk=user.pk).exists())
