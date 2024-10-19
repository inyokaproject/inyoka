"""
    tests.apps.forum.test_views
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test forum views.

    :copyright: (c) 2012-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import datetime
import shutil
import zoneinfo
from os import makedirs, path
from random import randint
from unittest.mock import patch

import feedparser
import responses
from django.conf import settings
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.http import Http404
from django.test import RequestFactory
from django.test.utils import override_settings
from django.utils import timezone, translation
from django.utils.dateparse import parse_datetime
from django.utils.translation import gettext as _
from freezegun import freeze_time
from guardian.shortcuts import assign_perm, remove_perm

from inyoka.forum import constants, views
from inyoka.forum.constants import get_distro_choices, get_version_choices
from inyoka.forum.models import (
    Attachment,
    Forum,
    Poll,
    PollOption,
    Post,
    Topic,
)
from inyoka.portal.user import User
from inyoka.portal.utils import UbuntuVersion
from inyoka.utils.storage import storage
from inyoka.utils.test import AntiSpamTestCaseMixin, InyokaClient, TestCase
from inyoka.utils.urls import href, url_for


class TestViews(AntiSpamTestCaseMixin, TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()
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
        self.post = Post.objects.create(text='Post 1', author=self.user,
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
            for i in range(1, randint(2, 3)):
                posts.append(Post(
                    text="More Posts %s" % randint(1, 100000), topic=t,
                    author=self.user, position=i,
                ))
            for i in range(1, randint(2, 3)):
                posts.append(Post(
                    text="More Posts %s" % randint(1, 100000), topic=t,
                    author=self.admin, position=i,
                ))

        self.num_topics_on_last_page = int(round(constants.TOPICS_PER_PAGE * 0.66))
        for i in range(1, 4 * constants.TOPICS_PER_PAGE + self.num_topics_on_last_page):
            newtopic()
        Post.objects.bulk_create(posts)

    def test_reported_topics(self):
        response = self.client.get('/reported_topics/')
        self.assertEqual(response.status_code, 200)

    @patch('inyoka.forum.views.send_notification')
    def test_movetopic(self, mock_send):
        self.assertEqual(Topic.objects.get(id=self.topic.id).forum_id, self.forum2.id)
        response = self.client.post('/topic/%s/move/' % self.topic.slug, {'forum': self.forum3.id})
        self.assertEqual(response.status_code, 302)

        self.assertEqual(mock_send.call_count, 1)  # only the topic author
        mock_send.assert_called_with(
            self.user,
            'topic_moved',
            _('Your topic “%(topic)s” was moved.') % {'topic': 'A test Topic'},
            {
                'username': self.user.username,
                'topic': self.topic,
                'mod': self.admin.username,
                'forum_name': 'Forum 3',
                'old_forum_name': 'Forum 2'
            }
        )

        self.assertEqual(Topic.objects.get(id=self.topic.id).forum_id, self.forum3.id)

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

    @patch('inyoka.forum.views.TOPICS_PER_PAGE', 4)
    @patch('inyoka.forum.constants.TOPICS_PER_PAGE', 4)
    def test_topiclist(self):
        self._setup_pagination()
        self.assertEqual(len(self.client.get("/last24/").context['topics']),
                         constants.TOPICS_PER_PAGE)
        self.assertEqual(len(self.client.get("/last24/3/").context['topics']),
                         constants.TOPICS_PER_PAGE)
        self.assertEqual(len(self.client.get("/last24/5/").context['topics']),
                         self.num_topics_on_last_page)
        self.assertTrue(self.client.get("/last24/6/").status_code == 404)

    def test_service_splittopic(self):
        t1 = Topic.objects.create(title='A: topic', slug='a:-topic',
                author=self.user, forum=self.forum2)
        p1 = Post.objects.create(text='Post 1', author=self.user,
                topic=t1)

        t2 = Topic.objects.create(title='Another topic', author=self.user,
                forum=self.forum2)
        p2 = Post.objects.create(text='Post 1', author=self.user,
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
        p11 = Post.objects.create(text='Post 1-1', author=self.user,
                topic=t1, position=0)
        p12 = Post.objects.create(text='Post 1-2', author=self.user,
                topic=t1)
        p13 = Post.objects.create(text='Post 1-3', author=self.user,
                topic=t1)

        t2 = Topic.objects.create(title='Topic 2', slug='topic-2',
                author=self.user, forum=self.forum2)
        p21 = Post.objects.create(text='Post 2-1', author=self.user,
                topic=t2, position=0)
        p22 = Post.objects.create(text='Post 2-2', author=self.user,
                topic=t2)
        p23 = Post.objects.create(text='Post 2-3', author=self.user,
                topic=t2)

        self.client.get('/', {
            '__service__': 'forum.mark_topic_split_point',
            'post': p12.pk,
            'from_here': 'true',
            'topic': t1.slug})
        self.client.post('/topic/%s/split/' % t1.slug, {
            'action': 'add',
            'topic_to_move': t2.slug})

        # The order in Topic 2 should now be
        # p21 p22 p23 p12 p13
        self.assertEqual(Post.objects.filter(topic_id=t1.pk).count(), 1)
        self.assertEqual(Post.objects.filter(topic_id=t2.pk).count(), 5)
        self.assertEqual(valuelist(t1.pk), [p11.pk])
        self.assertEqual(valuelist(t2.pk), [p21.pk, p22.pk, p23.pk, p12.pk, p13.pk])
        self.assertEqual(valuelist(t1.pk, 'position'), [0])
        self.assertEqual(valuelist(t2.pk, 'position'), list(range(0, 5)))

        # We will now strip all posts beginning at p22 from t2
        self.client.get('/', {
            '__service__': 'forum.mark_topic_split_point',
            'post': p22.pk,
            'from_here': 'true',
            'topic': t2.slug})
        self.client.post('/topic/%s/split/' % t2.slug, {
            'action': 'add',
            'topic_to_move': t1.slug})
        # The order in Topic 1 should now be
        # p11 p22 p23 p12 p13
        # Previously it was
        # for Topic 1 p11 p22 p23 and for Topic 2 p21 p12 p13
        self.assertEqual(Post.objects.filter(topic_id=t1.pk).count(), 5)
        self.assertEqual(Post.objects.filter(topic_id=t2.pk).count(), 1)
        self.assertEqual(valuelist(t1.pk), [p11.pk, p22.pk, p23.pk, p12.pk, p13.pk])
        self.assertEqual(valuelist(t2.pk), [p21.pk])
        self.assertEqual(valuelist(t1.pk, 'position'), list(range(0, 5)))
        self.assertEqual(valuelist(t2.pk, 'position'), [0])

    @responses.activate
    @override_settings(INYOKA_USE_AKISMET=True)
    def test_topic_mark_ham_admin(self):
        topic = Topic.objects.create(
            title='A test Topic', author=self.user, forum=self.forum2,
            hidden=True, reported='spam', reporter=self.system_user,
        )
        post = Post.objects.create(
            text='Post 1', author=self.user, topic=topic, position=0, hidden=False
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
            text='Post 1', author=self.user, topic=topic, position=0,
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
            text='Post 1', author=self.user, topic=topic, position=0
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
            text='Post 1', author=self.user, topic=topic, position=0
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
            text='Post 2', author=self.user, topic=self.topic, position=1, hidden=True
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
            text='Post 2', author=self.user, topic=self.topic, position=1, hidden=False
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
            text='Post 2', author=self.user, topic=self.topic, position=1, hidden=True
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
            text='Post 2', author=self.user, topic=self.topic, position=1, hidden=False
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
        super().setUp()
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

        self.client.post(f'/post/{post2.id}/hide/', {'confirm': 'yes'})

        self.assertEqual(self.user.post_count.value(), 1)

    def test_show_post(self):
        """
        Tests that the user post counter is increased, when a post is un hidden.
        """
        topic = Topic.objects.create(forum=self.forum, author=self.user)
        Post.objects.create(author=self.user, topic=topic)
        post2 = Post.objects.create(author=self.user, topic=topic, hidden=True)
        cache.set(self.user.post_count.cache_key, 1)

        self.client.post(f'/post/{post2.id}/restore/', {'confirm': 'yes'})

        self.assertEqual(self.user.post_count.value(), 2)

    def test_delete_hidden_post(self):
        """
        Tests that the post counter is not chaned when a hidden post is deleted.
        """
        topic = Topic.objects.create(forum=self.forum, author=self.user)
        Post.objects.create(author=self.user, topic=topic)
        post2 = Post.objects.create(author=self.user, topic=topic, hidden=True)
        cache.set(self.user.post_count.cache_key, 1)

        self.client.post(f'/post/{post2.id}/delete/', {'confirm': 'yes'})

        self.assertEqual(self.user.post_count.value(), 1)


class TestPostEditView(AntiSpamTestCaseMixin, TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()
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
            polls=None, polloptions=None, submit=False, fail_if_post_count_differs=True):
        """
        fail_if_post_count_differs: If true, an AssertionError is raised, if the resulting topic has more posts than given as parameter post.
            If the topic contains posts of previous submits, you need to set this parameter to False.
        """
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
        if fail_if_post_count_differs:
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
        }, response.content.decode(), count=1)

    def assertPreviewInHTML(self, text, response):
        pattern = '<div class="preview_wrapper"><h2 class="title">Preview</h2><div class="preview"><p>%s</p></div></div>'
        content = response.content.decode()
        self.assertInHTML(pattern % text, content, count=1)

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

    def test_newtopic__text_whitespace_not_stripped(self):
        self.client.login(username='admin', password='admin')

        text = ' * a \n * b\n'
        postdata = {
            'title': 'newpost_title',
            'ubuntu_distro': constants.get_distro_choices()[2][0],
            'text': text,
        }

        # Test send
        self.post_request(f'/forum/{self.forum.slug}/newtopic/', postdata, 1, 1, submit=True)

        # Check that the content is in the database
        self.assertEqual(
            Topic.objects.get(slug='newpost-title').last_post.text,
            text,
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
        content = response.content.decode()

        self.assertInHTML('<div class="message info">Your submission needs approval '
                          'by a team member and is hidden meanwhile. Please be patient, '
                          'we will get to it as soon as possible.</div>',
                          content, count=1)
        self.assertInHTML('<div class="message info">This topic is hidden. Either it '
                          'needs to be activated by moderators or it has been hidden '
                          'explicitly by moderators.</div>',
                          content, count=1)

    @responses.activate
    @override_settings(INYOKA_USE_AKISMET=True)
    def test_newtopic_user_spam_with_other_authors_post(self):
        """
        A hidden topic is visible to the author if all posts of that topic belong to the same user.
        This check adds a post by another user (admin) and the original poster should not be able to view it.
        See https://github.com/inyokaproject/inyoka/pull/1191
        """
        self.client.login(username='user', password='user')
        self.make_valid_key()
        self.make_spam()
        # Test preview
        postdata = {
            'title': 'newpost_title',
            'ubuntu_distro': constants.get_distro_choices()[2][0],
            'text': 'newpost text',
        }
        # Post it
        self.post_request('/forum/%s/newtopic/' % self.public_forum.slug, postdata, 1, 1, submit=True)

        self.client.logout()
        self.client.login(username='admin', password='admin')
        self.post_request('/topic/newpost-title/reply/', postdata, 1, 1, submit=True, fail_if_post_count_differs=False)
        self.client.logout()
        self.client.login(username='user', password='user')

        # Check for rendered post
        with translation.override('en-us'):
            response = self.client.get('/topic/newpost-title/')
        content = response.content.decode()
        self.assertInHTML('<div class="error"><p>You do not have permissions to access this page.</p></div>',
                          content, count=1)

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
        self.assertInHTML('Your submission needs approval by a team member', response.content.decode(), count=0)

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
        self.assertContains(response, 'Your submission needs approval by a team member', count=0)

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
        content = response.content.decode()
        self.assertInHTML('<div class="text"><p>newpost text</p></div>', content, count=1)
        att = Attachment.objects.get()
        pattern = '<li><a href="%(url)s" type="image/png" title="%(comment)s">Download %(name)s</a></li>'
        self.assertInHTML(pattern % {'url': att.get_absolute_url(), 'comment': att.comment, 'name': att.name}, content, count=1)

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
        self.assertInHTML('<div class="text"><p>newpost text</p></div>', response.content.decode(), count=1)
        att1, att2 = Attachment.objects.all()
        pattern = '<li><a href="%(url)s" type="image/png" title="%(comment)s">Download %(name)s</a></li>'
        content = response.content.decode()
        self.assertInHTML(pattern % {'url': att1.get_absolute_url(), 'comment': att1.comment, 'name': att1.name}, content, count=1)
        self.assertInHTML(pattern % {'url': att2.get_absolute_url(), 'comment': att2.comment, 'name': att2.name}, content, count=1)

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
        self.assertInHTML(pattern % {'q': poll.question, 'pk': poll.pk}, response.content.decode(), count=1)

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
        self.assertInHTML('<div class="text"><p>newpost text</p></div>', response.content.decode(), count=1)
        poll = Poll.objects.get()
        opt1, opt2 = PollOption.objects.all()
        pattern = '<tr><td><input type="radio" name="poll_%(poll_pk)d" id="option_%(opt_pk)d" value="%(opt_pk)d"/><label for="option_%(opt_pk)d">%(opt)s</label></td></tr>'
        content = response.content.decode()
        self.assertInHTML('<caption>%(question)s</caption>' % {'question': poll.question}, content, count=1)
        self.assertInHTML(pattern % {'poll_pk': poll.pk, 'opt': opt1.name, 'opt_pk': opt1.pk}, content, count=1)
        self.assertInHTML(pattern % {'poll_pk': poll.pk, 'opt': opt2.name, 'opt_pk': opt2.pk}, content, count=1)

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
        content = response.content.decode()
        self.assertInHTML(pattern % {'q': poll1.question, 'pk': poll1.pk}, content, count=1)
        self.assertInHTML(pattern % {'q': poll2.question, 'pk': poll2.pk}, content, count=1)

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

    def test_vote_in_poll(self):
        self.client.login(username='admin', password='admin')
        # Add first poll
        postdata = {
            'question': "What shall I ask?",
            'options': ['this', 'that'],
            'add_poll': True,
        }
        self.post_request('/forum/%s/newtopic/' % self.forum.slug, postdata, 0, 0, polls=1, polloptions=2)
        poll = Poll.objects.get()

        # create topic for poll
        postdata = {
            'title': 'newpost_title',
            'ubuntu_distro': constants.get_distro_choices()[2][0],
            'text': 'newpost text',
            'polls': str(poll.pk),
        }
        self.post_request('/forum/%s/newtopic/' % self.forum.slug, postdata, 1, 1, polls=1, polloptions=2, submit=True)

        # submit vote
        postdata = {
            'poll_%s' % poll.id: poll.options.first().id,
            'vote': 'submit'
        }
        self.client.post('/topic/newpost-title/', postdata)
        self.assertEqual(poll.votes, 1)

    def test_new_post(self):
        topic = Topic.objects.create(title='topic', author=self.admin, forum=self.forum)
        Post.objects.create(text='first post', author=self.admin, position=0, topic=topic)

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

    def test_new_post__text_whitespace_not_stripped(self):
        topic = Topic.objects.create(title='topic', author=self.admin, forum=self.forum)
        Post.objects.create(text='first post', author=self.admin, topic=topic)

        self.client.login(username='admin', password='admin')
        text = ' * a \n * b\n'
        postdata = {
            'text': text,
        }

        # Test send
        self.post_request(f'/topic/{topic.slug}/reply/', postdata, 1, 2, submit=True)

        # Test that the data is in the database
        topic.refresh_from_db()
        self.assertEqual(
            topic.last_post.text,
            text,
        )

    def test_new_post_user(self):
        topic = Topic.objects.create(title='topic', author=self.admin, forum=self.forum)
        Post.objects.create(text='first post', author=self.admin, position=0, topic=topic)

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
        Post.objects.create(text='first post', author=self.admin, position=0, topic=topic)

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
        content = response.content.decode()
        self.assertInHTML('<div class="message info">Your submission needs approval by a '
                          'team member and is hidden meanwhile. Please be patient, we will '
                          'get to it as soon as possible. </div>',
                          content, count=1)
        self.assertInHTML('<div class="text"><p>newpost text</p></div>', content, count=1)

    @responses.activate
    @override_settings(INYOKA_USE_AKISMET=True)
    def test_new_post_frequent_user_spam(self):
        # frequent users (>100 posts) should be excluded from spam detection
        cache.set(self.user.post_count.cache_key, 100)
        topic = Topic.objects.create(title='topic', author=self.admin, forum=self.public_forum)
        Post.objects.create(text='first post', author=self.admin, position=0, topic=topic)

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
        self.assertInHTML('Your submission needs approval by a team member', response.content.decode(), count=0)

    @responses.activate
    @override_settings(INYOKA_USE_AKISMET=True)
    def test_new_post_user_spam_non_public(self):
        topic = Topic.objects.create(title='topic', author=self.admin, forum=self.forum)
        Post.objects.create(text='first post', author=self.admin, position=0, topic=topic)

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
        self.assertContains(response, 'Your submission needs approval by a team member', count=0)
        self.assertInHTML('<div class="text"><p>newpost text</p></div>', response.content.decode(),
                          count=1)

    def test_new_post_with_file(self):
        topic = Topic.objects.create(title='topic', author=self.admin, forum=self.forum)
        Post.objects.create(text='first post', author=self.admin, position=0, topic=topic)

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
        content = response.content.decode()
        self.assertInHTML('<div class="text"><p>newpost text</p></div>', content, count=1)
        att = Attachment.objects.get()
        pattern = '<li><a href="%(url)s" type="image/png" title="%(comment)s">Download %(name)s</a></li>'
        self.assertInHTML(pattern % {'url': att.get_absolute_url(), 'comment': att.comment, 'name': att.name}, content, count=1)

    def test_new_post_with_multiple_files(self):
        topic = Topic.objects.create(title='topic', author=self.admin, forum=self.forum)
        Post.objects.create(text='first post', author=self.admin, position=0, topic=topic)

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
        self.assertInHTML('<div class="text"><p>newpost text</p></div>', response.content.decode(),
                          count=1)
        att1, att2 = Attachment.objects.all()
        pattern = '<li><a href="%(url)s" type="image/png" title="%(comment)s">Download %(name)s</a></li>'
        content = response.content.decode()
        self.assertInHTML(pattern % {'url': att1.get_absolute_url(), 'comment': att1.comment, 'name': att1.name}, content, count=1)
        self.assertInHTML(pattern % {'url': att2.get_absolute_url(), 'comment': att2.comment, 'name': att2.name}, content, count=1)

    def test_edit_post(self):
        topic = Topic.objects.create(title='topic', author=self.admin, forum=self.forum)
        Post.objects.create(text='first post', author=self.admin, position=0, topic=topic)
        post = Post.objects.create(text='second post', author=self.admin, position=1, topic=topic)

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
        self.assertInHTML('<div class="text"><p>editpost text</p></div>', response.content.decode(), count=1)

    def test_edit_post_user(self):
        topic = Topic.objects.create(title='topic', author=self.admin, forum=self.forum)
        Post.objects.create(text='first post', author=self.admin, position=0, topic=topic)
        post = Post.objects.create(text='second post', author=self.user, position=1, topic=topic)

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
        self.assertInHTML('<div class="text"><p>editpost text</p></div>', response.content.decode(), count=1)

    @responses.activate
    @override_settings(INYOKA_USE_AKISMET=True)
    def test_edit_post_user_spam(self):
        # Edited posts are never considered spam, not even from users
        topic = Topic.objects.create(title='topic', author=self.admin, forum=self.public_forum)
        Post.objects.create(text='first post', author=self.admin, position=0, topic=topic)
        post = Post.objects.create(text='second post', author=self.user, position=1, topic=topic)

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
        self.assertInHTML('<div class="text"><p>editpost text</p></div>', response.content.decode(), count=1)

    @responses.activate
    @override_settings(INYOKA_USE_AKISMET=True)
    def test_edit_post_user_spam_non_public(self):
        topic = Topic.objects.create(title='topic', author=self.admin, forum=self.forum)
        Post.objects.create(text='first post', author=self.admin, position=0, topic=topic)
        post = Post.objects.create(text='second post', author=self.user, position=1, topic=topic)

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
        self.assertContains(response, 'Your submission needs approval by a team member', count=0)
        self.assertInHTML('<div class="text"><p>editpost text</p></div>', response.content.decode(), count=1)

    def test_edit_post_remove_attachments(self):
        TEST_ATTACHMENT1 = 'test_attachment.png'
        TEST_ATTACHMENT2 = 'test_attachment2.png'
        self.client.login(username='admin', password='admin')

        topic = Topic.objects.create(title='topic', author=self.admin, forum=self.forum)
        Post.objects.create(text='first post', author=self.admin, position=0, topic=topic)
        post = Post.objects.create(text='second post', author=self.admin, position=1, topic=topic)

        basedir = path.join(settings.MEDIA_ROOT, 'forum', 'attachments', '00', '00')
        if not path.exists(basedir):
            makedirs(basedir)
        new_file1 = path.join(basedir, TEST_ATTACHMENT1)
        shutil.copy(path.join(path.dirname(__file__), TEST_ATTACHMENT1), new_file1)
        new_file2 = path.join(basedir, TEST_ATTACHMENT2)
        shutil.copy(path.join(path.dirname(__file__), TEST_ATTACHMENT2), new_file2)

        att1 = Attachment.objects.create(name=TEST_ATTACHMENT1, file=path.relpath(new_file1, start=settings.MEDIA_ROOT), mimetype='image/png', post=post)
        att2 = Attachment.objects.create(name=TEST_ATTACHMENT2, file=path.relpath(new_file2, start=settings.MEDIA_ROOT), mimetype='image/png', post=post)
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
        self.assertInHTML('<textarea id="id_text" rows="10" cols="40" name="text">edit 1</textarea>',
                          response.content.decode())
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
        self.assertInHTML('<textarea id="id_text" rows="10" cols="40" name="text">edit 2</textarea>',
                          response.content.decode())

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
        self.assertInHTML('<div class="text"><p>edit 3</p></div>', response.content.decode(), count=1)

    def test_edit_first_post(self):
        topic = Topic.objects.create(title='topic', author=self.admin, forum=self.forum)
        post = Post.objects.create(text='first post', author=self.admin, position=0, topic=topic)

        self.client.login(username='admin', password='admin')
        # Test preview
        postdata = {
            'title': 'edited title',
            'text': 'edited text',
        }
        response = self.post_request('/post/%d/edit/' % post.pk, postdata, 1, 1)
        content = response.content.decode()
        self.assertInHTML('<input type="text" name="title" value="edited title" required maxlength="100" id="id_title" size="60" />', content)
        self.assertPreviewInHTML('edited text', response)

        # Test send
        self.post_request('/post/%d/edit/' % post.pk, postdata, 1, 1, submit=True)

        # Check for rendered post
        with translation.override('en-us'):
            response = self.client.get('/topic/%s/' % topic.slug)
        content = response.content.decode()
        self.assertInHTML('<h2>edited title</h2>', content, count=1)
        self.assertInHTML('<div class="text"><p>edited text</p></div>', content, count=1)

    def test_edit_first_post_user(self):
        topic = Topic.objects.create(title='topic', author=self.user, forum=self.forum)
        post = Post.objects.create(text='first post', author=self.user, position=0, topic=topic)

        self.client.login(username='user', password='user')
        # Test preview
        postdata = {
            'title': 'edited title',
            'text': 'edited text',
        }
        response = self.post_request('/post/%d/edit/' % post.pk, postdata, 1, 1)
        self.assertInHTML('<input type="text" name="title" value="edited title" required maxlength="100" id="id_title" size="60" />',
                          response.content.decode())
        self.assertPreviewInHTML('edited text', response)

        # Test send
        self.post_request('/post/%d/edit/' % post.pk, postdata, 1, 1, submit=True)

        # Check for rendered post
        with translation.override('en-us'):
            response = self.client.get('/topic/%s/' % topic.slug)
        content = response.content.decode()
        self.assertInHTML('<h2>edited title</h2>', content, count=1)
        self.assertInHTML('<div class="text"><p>edited text</p></div>', content, count=1)

    @responses.activate
    @override_settings(INYOKA_USE_AKISMET=True)
    def test_edit_first_post_user_spam(self):
        # Edited posts are never considered spam, not even from users
        topic = Topic.objects.create(title='topic', author=self.user, forum=self.public_forum)
        post = Post.objects.create(text='first post', author=self.user, position=0, topic=topic)

        self.client.login(username='user', password='user')
        self.make_valid_key()
        self.make_spam()
        # Test preview
        postdata = {
            'title': 'edited title',
            'text': 'edited text',
        }
        response = self.post_request('/post/%d/edit/' % post.pk, postdata, 1, 1)
        self.assertInHTML('<input type="text" name="title" value="edited title" required maxlength="100" id="id_title" size="60" />',
                          response.content.decode())
        self.assertPreviewInHTML('edited text', response)

        # Test send
        self.post_request('/post/%d/edit/' % post.pk, postdata, 1, 1, submit=True)

        # Check for rendered post
        with translation.override('en-us'):
            response = self.client.get('/topic/%s/' % topic.slug)
        content = response.content.decode()
        self.assertInHTML('<h2>edited title</h2>', content, count=1)
        self.assertInHTML('<div class="text"><p>edited text</p></div>', content, count=1)

    @responses.activate
    @override_settings(INYOKA_USE_AKISMET=True)
    def test_edit_first_post_user_spam_non_public(self):
        topic = Topic.objects.create(title='topic', author=self.user, forum=self.forum)
        post = Post.objects.create(text='first post', author=self.user, position=0, topic=topic)

        self.client.login(username='user', password='user')
        self.make_valid_key()
        self.make_spam()
        # Test preview
        postdata = {
            'title': 'edited title',
            'text': 'edited text',
        }
        response = self.post_request('/post/%d/edit/' % post.pk, postdata, 1, 1)
        self.assertInHTML('<input type="text" name="title" value="edited title" required maxlength="100" id="id_title" size="60" />',
                          response.content.decode())
        self.assertPreviewInHTML('edited text', response)

        # Test send
        self.post_request('/post/%d/edit/' % post.pk, postdata, 1, 1, submit=True)

        # Check for rendered post
        with translation.override('en-us'):
            response = self.client.get('/topic/%s/' % topic.slug)
        self.assertContains(response, 'Your submission needs approval by a team member', count=0)
        self.assertInHTML('<div class="text"><p>edited text</p></div>', response.content.decode(), count=1)

    def test_edit_first_post_remove_polls(self):
        topic = Topic.objects.create(title='topic', author=self.admin, forum=self.forum)
        post = Post.objects.create(text='first post', author=self.admin, position=0, topic=topic)
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
        content = response.content.decode()
        self.assertInHTML(pattern % {'q': poll1.question, 'pk': poll1.pk}, content, count=1)
        self.assertInHTML(pattern % {'q': poll2.question, 'pk': poll2.pk}, content, count=1)

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
        content = response.content.decode()
        self.assertInHTML(pattern % {'q': poll2.question, 'pk': poll2.pk}, content, count=1)
        self.assertInHTML('<input type="text" name="title" value="edited title" required maxlength="100" id="id_title" size="60" />', content)

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
        self.assertInHTML('<input type="text" name="title" value="edited title 2" required maxlength="100" id="id_title" size="60" />',
                          response.content.decode())

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
        content = response.content.decode()
        self.assertInHTML('<h2>edited title 4</h2>', content, count=1)
        self.assertInHTML('<div class="text"><p>edited text 4</p></div>', content, count=1)


class TestWelcomeMessageView(TestCase):

    def setUp(self):
        super().setUp()
        self.user = User.objects.register_user('user', 'user@example.com', 'user', False)
        self.forum_welcome = Forum.objects.create(slug='f-slug-welcome', welcome_title='test')
        self.forum_no_welcome = Forum.objects.create(slug='f-slug-no-welcome')
        registered_group = Group.objects.get(name=settings.INYOKA_REGISTERED_GROUP_NAME)
        for forum in (self.forum_welcome, self.forum_no_welcome):
            assign_perm('forum.view_forum', registered_group, forum)

    def test_post_accept(self):
        request = RequestFactory().post('/fake/', {'accept': True})
        request.user = self.user

        response = views.WelcomeMessageView.as_view()(request, slug='f-slug-welcome')

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], url_for(self.forum_welcome))
        self.assertTrue(self.forum_welcome.welcome_read_users.filter(pk=self.user.pk).exists())

    def test_post_not_deny(self):
        request = RequestFactory().post('/fake/', {})
        request.user = self.user

        response = views.WelcomeMessageView.as_view()(request, slug='f-slug-welcome')

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], href('forum'))
        self.assertFalse(self.forum_welcome.welcome_read_users.filter(pk=self.user.pk).exists())

    def test_forum_has_no_welcome_message(self):
        request = RequestFactory().get('/fake/')
        request.user = self.user

        with self.assertRaises(Http404):
            views.WelcomeMessageView.as_view()(request, slug='f-slug-no-welcome')

        self.assertFalse(self.forum_no_welcome.welcome_read_users.filter(pk=self.user.pk).exists())


class TestMarkRead(TestCase):

    def setUp(self) -> None:
        super().setUp()
        self.public_category = Forum.objects.create(name='Public category')
        self.public_forum = Forum.objects.create(name='Public forum', parent=self.public_category)

        self.user = User.objects.register_user('user', 'user@example.test', 'user', False)
        registered_group = Group.objects.get(name=settings.INYOKA_REGISTERED_GROUP_NAME)
        assign_perm('forum.view_forum', registered_group, self.public_category)
        assign_perm('forum.view_forum', registered_group, self.public_forum)

        topic = Topic.objects.create(title='A test Topic', author=self.user, forum=self.public_forum)
        Post.objects.create(text='Post 1', author=self.user, topic=topic, position=0)

        self.client.defaults['HTTP_HOST'] = 'forum.%s' % settings.BASE_DOMAIN_NAME

    def test_anonymous(self):
        url = self.public_forum.get_absolute_url('markread')
        response = self.client.get(url, follow=True)

        self.assertRedirects(response, href('forum'))
        self.assertContains(response, 'Please login to mark posts as read.')

    def test_mark_all_as_read(self):
        self.client.force_login(user=self.user)

        url = href('forum', 'markread')
        response = self.client.get(url, follow=True)

        self.assertRedirects(response, href('forum'))
        self.assertContains(response, 'All forums were marked as read.')

    def test_mark_one_forum(self):
        self.client.force_login(user=self.user)

        url = self.public_forum.get_absolute_url('markread')
        response = self.client.get(url, follow=True)

        self.assertRedirects(response, url_for(self.public_forum))
        self.assertContains(response, f'The forum “{self.public_forum.name}” was marked as read.')

    def test_no_existing_forum(self):
        self.client.force_login(user=self.user)

        url = href('forum', 'forum', 'does_not_exist', 'markread')
        response = self.client.get(url, follow=True)

        self.assertEqual(response.status_code, 404)


@freeze_time("2023-12-09T23:55:04Z")
class TestPostFeed(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()

        self.now = timezone.now()

        self.user = User.objects.register_user('user', 'user', 'user', False)

        self.forum = Forum.objects.create(name='forum')

        self.anonymous_group = Group.objects.get(name=settings.INYOKA_ANONYMOUS_GROUP_NAME)
        assign_perm('forum.view_forum', self.anonymous_group, self.forum)
        self.topic = Topic.objects.create(forum=self.forum, author=self.user, title='test topic')
        Post.objects.create(author=self.user, topic=self.topic, text='some text', pub_date=self.now)

        self.client.defaults['HTTP_HOST'] = 'forum.%s' % settings.BASE_DOMAIN_NAME

    def test_no_allowed_forum(self):
        anonymous_group = Group.objects.get(name=settings.INYOKA_ANONYMOUS_GROUP_NAME)
        remove_perm('forum.view_forum', anonymous_group, self.forum)

        response = self.client.get('/feeds/short/10/', follow=True)
        self.assertEqual(response.status_code, 403)

    def test_modes(self):
        response = self.client.get('/feeds/short/10/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/feeds/title/20/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/feeds/full/50/')
        self.assertEqual(response.status_code, 200)

    def test_queries(self):
        with self.assertNumQueries(9):
            self.client.get('/feeds/full/50/')

    def test_topic_hidden(self):
        """Hide the only topic, so the feed should not contain any topics"""
        self.topic.hidden = True
        self.topic.save()

        response = self.client.get('/feeds/full/10/')
        feed = feedparser.parse(response.content)
        self.assertEqual(len(feed.entries), 0)

    def test_multiple_topics(self):
        topic = Topic.objects.create(forum=self.forum, author=self.user, title='another topic')
        Post.objects.create(author=self.user, topic=topic, text='another text', pub_date=self.now)

        response = self.client.get('/feeds/full/10/')
        self.assertIn(self.topic.title, response.content.decode())

        feed = feedparser.parse(response.content)
        self.assertEqual(len(feed.entries), 2)

    def test_categories(self):
        child_forum = Forum.objects.create(parent=self.forum, name='child')
        self.topic.forum = child_forum

        version = UbuntuVersion('22.04', 'Jammy Jellyfish', lts=True, active=True, current=True)
        storage['distri_versions'] = f'[{version.as_json()}]'

        self.topic.ubuntu_version = get_version_choices()[1][0]
        self.topic.ubuntu_distro = get_distro_choices()[2][0]
        self.topic.save()

        assign_perm('forum.view_forum', self.anonymous_group, child_forum)

        response = self.client.get('/feeds/full/10/')
        feed = feedparser.parse(response.content)
        self.assertEqual(len(feed.entries), 1)

        terms = [t['term'] for t in feed.entries[0]['tags']]
        self.assertSequenceEqual(terms, ['child', 'forum', '22.04 (Jammy Jellyfish)', 'Edubuntu 22.04 (Jammy Jellyfish)'])

    def test_content_exact(self):
        response = self.client.get('/feeds/full/10/')

        self.maxDiff = None
        self.assertXMLEqual(response.content.decode(),
'''<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="en-us">
  <title>ubuntuusers.local:8080 forum</title>
  <link href="http://forum.ubuntuusers.local:8080/" rel="alternate" />
  <link href="http://forum.ubuntuusers.local:8080/feeds/full/10/" rel="self" />
  <id>http://forum.ubuntuusers.local:8080/</id>
  <updated>2023-12-10T00:55:04+01:00</updated>
  <subtitle>Feed contains new topics of the whole forum</subtitle>
  <rights>http://ubuntuusers.local:8080/lizenz/</rights>
  <entry>
    <title>test topic</title>
    <link href="http://forum.ubuntuusers.local:8080/topic/test-topic/" rel="alternate"/>
    <published>2023-12-10T00:55:04+01:00</published>
    <updated>2023-12-10T00:55:04+01:00</updated>
    <author>
      <name>user</name>
      <uri>http://ubuntuusers.local:8080/user/user/</uri>
    </author>
    <id>http://forum.ubuntuusers.local:8080/topic/test-topic/</id>
    <summary type="html">&lt;p&gt;some text&lt;/p&gt;</summary>
    <category term="forum"/>
    <category term="Not specified"/>
  </entry>
</feed>
''')


@freeze_time("2023-12-09T23:55:04Z")
class TestPostForumFeed(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()

        self.now = timezone.now()

        self.user = User.objects.register_user('user', 'user', 'user', False)

        self.forum = Forum.objects.create(name='hardware')

        anonymous_group = Group.objects.get(name=settings.INYOKA_ANONYMOUS_GROUP_NAME)
        assign_perm('forum.view_forum', anonymous_group, self.forum)
        self.topic = Topic.objects.create(forum=self.forum, author=self.user, title='test topic')
        Post.objects.create(author=self.user, topic=self.topic, text='some text', pub_date=self.now)

        self.client.defaults['HTTP_HOST'] = 'forum.%s' % settings.BASE_DOMAIN_NAME

    def test_not_allowed_forum(self):
        anonymous_group = Group.objects.get(name=settings.INYOKA_ANONYMOUS_GROUP_NAME)
        remove_perm('forum.view_forum', anonymous_group, self.forum)

        response = self.client.get(f'/feeds/forum/{self.forum.name}/short/10/', follow=True)
        self.assertEqual(response.status_code, 403)

    def test_modes(self):
        response = self.client.get(f'/feeds/forum/{self.forum.name}/short/10/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(f'/feeds/forum/{self.forum.name}/title/20/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(f'/feeds/forum/{self.forum.name}/full/50/')
        self.assertEqual(response.status_code, 200)

    def test_queries(self):
        with self.assertNumQueries(9):
            self.client.get(f'/feeds/forum/{self.forum.name}/full/50/')

    def test_child_forum(self):
        child_forum = Forum.objects.create(name='sub hardware', parent=self.forum)
        self.assertEqual(len(self.forum.children), 1)

        anonymous_group = Group.objects.get(name=settings.INYOKA_ANONYMOUS_GROUP_NAME)
        assign_perm('forum.view_forum', anonymous_group, child_forum)
        topic = Topic.objects.create(forum=child_forum, author=self.user, title='test topic')
        post = Post.objects.create(author=self.user, topic=topic, text='foo text', pub_date=self.now)

        response = self.client.get(f'/feeds/forum/{self.forum.name}/full/50/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(post.text, response.content.decode())

    def test_topic_hidden(self):
        """Hide the only topic, so the feed should not contain any topics"""
        self.topic.hidden = True
        self.topic.save()

        response = self.client.get(f'/feeds/forum/{self.forum.name}/full/10/')
        feed = feedparser.parse(response.content)
        self.assertEqual(len(feed.entries), 0)

    def test_invalid_forum_slug(self):
        response = self.client.get('/feeds/forum/fooBarBAZ/short/10/', follow=True)
        self.assertEqual(response.status_code, 404)

    def test_multiple_topics(self):
        topic = Topic.objects.create(forum=self.forum, author=self.user, title='another topic')
        Post.objects.create(author=self.user, topic=topic, text='another text', pub_date=self.now)

        response = self.client.get(f'/feeds/forum/{self.forum.name}/full/10/')
        self.assertIn(self.topic.title, response.content.decode())

        feed = feedparser.parse(response.content)
        self.assertEqual(len(feed.entries), 2)

    def test_content_exact(self):
        response = self.client.get(f'/feeds/forum/{self.forum.name}/full/10/')

        self.maxDiff = None
        self.assertXMLEqual(response.content.decode(),
'''<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="en-us">
  <title>ubuntuusers.local:8080 forum – “hardware”</title>
  <link href="http://forum.ubuntuusers.local:8080/category/hardware/" rel="alternate" />
  <link href="http://forum.ubuntuusers.local:8080/feeds/forum/hardware/full/10/" rel="self" />
  <id>http://forum.ubuntuusers.local:8080/category/hardware/</id>
  <updated>2023-12-10T00:55:04+01:00</updated>
  <subtitle>Feed contains new topics of the forum “hardware”.</subtitle>
  <rights>http://ubuntuusers.local:8080/lizenz/</rights>
  <entry>
    <title>test topic</title>
    <link href="http://forum.ubuntuusers.local:8080/topic/test-topic/" rel="alternate"/>
    <published>2023-12-10T00:55:04+01:00</published>
    <updated>2023-12-10T00:55:04+01:00</updated>
    <author>
      <name>user</name>
      <uri>http://ubuntuusers.local:8080/user/user/</uri>
    </author>
    <id>http://forum.ubuntuusers.local:8080/topic/test-topic/</id>
    <summary type="html">&lt;p&gt;some text&lt;/p&gt;</summary>
    <category term="hardware"/>
    <category term="Not specified"/>
  </entry>
</feed>
''')


class TestTopicFeedPostRevision(TestCase):
    """
    Test feed with a post that has two revisions.

    Only freeze setUp to a date in history, as the PostRevisions hardcodes utcnow.
    """

    client_class = InyokaClient

    @freeze_time("2023-12-09T23:55:04Z")
    def setUp(self):
        super().setUp()

        now = datetime.datetime.now().replace(microsecond=0)

        self.user = User.objects.register_user('user', 'user', 'user', False)
        self.forum = Forum.objects.create(name='hardware')

        anonymous_group = Group.objects.get(name=settings.INYOKA_ANONYMOUS_GROUP_NAME)
        assign_perm('forum.view_forum', anonymous_group, self.forum)
        self.topic = Topic.objects.create(forum=self.forum, author=self.user, title='test topic')
        self.post = Post.objects.create(author=self.user, topic=self.topic, text='some text', pub_date=now)

        self.client.defaults['HTTP_HOST'] = 'forum.%s' % settings.BASE_DOMAIN_NAME

    def test_post_multiple_revision_update_date(self):
        self.post.edit(text='foo')
        now_utc = datetime.datetime.utcnow().replace(tzinfo=zoneinfo.ZoneInfo("UTC"), microsecond=0)

        response = self.client.get(f'/feeds/topic/{self.topic.slug}/short/10/', follow=True)
        feed = feedparser.parse(response.content)

        feed_updated = parse_datetime(feed.entries[0].updated).replace(microsecond=0)
        self.assertEqual(feed_updated, now_utc)


@freeze_time("2023-12-09T23:55:04Z")
class TestTopicFeed(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()

        self.now = timezone.now()

        self.user = User.objects.register_user('user', 'user', 'user', False)

        self.forum = Forum.objects.create(name='hardware')

        anonymous_group = Group.objects.get(name=settings.INYOKA_ANONYMOUS_GROUP_NAME)
        assign_perm('forum.view_forum', anonymous_group, self.forum)
        self.topic = Topic.objects.create(forum=self.forum, author=self.user, title='test topic')
        Post.objects.create(author=self.user, topic=self.topic, text='some text', pub_date=self.now, id=1)

        self.client.defaults['HTTP_HOST'] = 'forum.%s' % settings.BASE_DOMAIN_NAME

    def test_modes(self):
        response = self.client.get(f'/feeds/topic/{self.topic.slug}/short/10/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(f'/feeds/topic/{self.topic.slug}/title/20/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(f'/feeds/topic/{self.topic.slug}/full/50/')
        self.assertEqual(response.status_code, 200)

    def test_queries(self):
        with self.assertNumQueries(9):
            self.client.get(f'/feeds/topic/{self.topic.slug}/full/50/')

    def test_multiple_posts(self):
        Post.objects.create(author=self.user, topic=self.topic, text='another text', pub_date=self.now)

        response = self.client.get(f'/feeds/topic/{self.topic.slug}/full/50/')
        self.assertIn(self.topic.title, response.content.decode())

        feed = feedparser.parse(response.content)
        self.assertEqual(len(feed.entries), 2)

    def test_post_with_control_characters(self):
        Post.objects.create(author=self.user, topic=self.topic, text='control characters \x08 \x0f in text',
                            pub_date=self.now)

        response = self.client.get(f'/feeds/topic/{self.topic.slug}/full/50/')
        self.assertIn(self.topic.title, response.content.decode())

    def test_topic_hidden(self):
        topic = Topic.objects.create(forum=self.forum, author=self.user, title='hidden topic', hidden=True)

        response = self.client.get(f'/feeds/topic/{topic.slug}/short/10/')
        self.assertEqual(response.status_code, 404)

    def test_post_hidden(self):
        """Create a second *hidden* post, so the feed should still only contain one post"""
        post = Post.objects.create(hidden=True, author=self.user, topic=self.topic, text='hidden text',
                                   pub_date=self.now)

        response = self.client.get(f'/feeds/topic/{self.topic.slug}/full/50/')
        self.assertNotIn(post.text, response.content.decode())

        feed = feedparser.parse(response.content)
        self.assertEqual(len(feed.entries), 1)

    def test_forum_no_permission(self):
        forum = Forum.objects.create(name='forum no perm')
        topic = Topic.objects.create(forum=forum, author=self.user, title='no perm topic')

        response = self.client.get(f'/feeds/topic/{topic.slug}/short/10/', follow=True)
        self.assertEqual(response.status_code, 403)

    def test_submitted_post_with_control_characters(self):
        """
        Test that control characters
          - get stripped from a post and
          - don't raise an exception upon visiting a feed
        """
        registered_group = Group.objects.get(name=settings.INYOKA_REGISTERED_GROUP_NAME)
        for privilege in ('forum.view_forum', 'forum.add_topic_forum', 'forum.add_reply_forum'):
            assign_perm(privilege, registered_group, self.forum)

        self.client.login(username='user', password='user')
        postdata = {
            'text': 'control characters \x08 \x0f in text',
            'send': True
        }
        self.client.post(f'/topic/{self.topic.slug}/reply/', postdata)

        self.topic.refresh_from_db()
        # \x08 and x0f should be stripped from the text
        self.assertEqual(self.topic.last_post.text, 'control characters   in text')

        self.client.get(f'/feeds/topic/{self.topic.slug}/full/50/')
        self.assertEqual(int(self.topic.post_count()), 2)

    def test_topic_title_control_characters(self):
        """
        Test that control characters
          - get stripped from a topic title and
          - don't raise an exception upon visiting a feed
        """
        self.subforum = Forum.objects.create(name='sub', parent=self.forum)

        registered_group = Group.objects.get(name=settings.INYOKA_REGISTERED_GROUP_NAME)
        for privilege in ('forum.view_forum', 'forum.add_topic_forum', 'forum.add_reply_forum'):
            assign_perm(privilege, registered_group, self.forum)
            assign_perm(privilege, registered_group, self.subforum)

        anonymous_group = Group.objects.get(name=settings.INYOKA_ANONYMOUS_GROUP_NAME)
        assign_perm('forum.view_forum', anonymous_group, self.subforum)

        self.client.login(username='user', password='user')

        postdata = {
           'title': 'control characters \x08 \x0f',
           'ubuntu_distro': constants.get_distro_choices()[2][0],
           'text': 'newpost text',
           'send': True
        }
        self.client.post('/forum/%s/newtopic/' % self.subforum.slug, postdata)

        response = self.client.get(f'/feeds/forum/{self.subforum.slug}/full/10/')
        self.assertContains(response, postdata['text'])

    def test_content_exact(self):
        response = self.client.get(f'/feeds/topic/{self.topic.slug}/full/50/')

        self.maxDiff = None
        self.assertXMLEqual(response.content.decode(),
'''<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="en-us">
  <title>ubuntuusers.local:8080 topic – “test topic”</title>
  <link href="http://forum.ubuntuusers.local:8080/topic/test-topic/" rel="alternate"/>
  <link href="http://forum.ubuntuusers.local:8080/feeds/topic/test-topic/full/50/" rel="self" />
  <id>http://forum.ubuntuusers.local:8080/topic/test-topic/</id>
  <updated>2023-12-10T00:55:04+01:00</updated>
  <subtitle>Feed contains posts of the topic “test topic”.</subtitle>
  <rights>http://ubuntuusers.local:8080/lizenz/</rights>
  <entry>
    <title>user (Dec. 10, 2023, 12:55 a.m.)</title>
    <link href="http://forum.ubuntuusers.local:8080/post/1/" rel="alternate"/>
    <published>2023-12-10T00:55:04+01:00</published>
    <updated>2023-12-10T00:55:04+01:00</updated>
    <author>
      <name>user</name>
      <uri>http://ubuntuusers.local:8080/user/user/</uri>
    </author>
    <id>http://forum.ubuntuusers.local:8080/post/1/</id>
    <summary type="html">&lt;p&gt;some text&lt;/p&gt;</summary>
  </entry>
</feed>
''')
