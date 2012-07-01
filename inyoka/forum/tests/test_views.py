#-*- coding: utf-8 -*-
from mock import patch
from random import randint
from os import path

from django.conf import settings
from django.test import TestCase

from inyoka.forum.acl import PRIVILEGES_BITS
from inyoka.forum import constants
from inyoka.forum.constants import TOPICS_PER_PAGE, VERSION_CHOICES, DISTRO_CHOICES
from inyoka.forum.models import Forum, Topic, Post, Privilege
from inyoka.portal.user import User, PERMISSION_NAMES
from inyoka.portal.models import Subscription
from inyoka.utils.test import InyokaClient, override_settings
from inyoka.utils.urls import href


class TestViews(TestCase):

    client_class = InyokaClient
    permissions = sum(PERMISSION_NAMES.keys())
    privileges = sum(PRIVILEGES_BITS.values())

    def setUp(self):
        self.admin = User.objects.register_user('admin', 'admin', 'admin', False)
        self.user = User.objects.register_user('user', 'user', 'user', False)
        self.admin._permissions = self.permissions
        self.admin.save()

        self.forum1 = Forum.objects.create(name='Forum 1')
        self.forum2 = Forum.objects.create(name='Forum 2', parent=self.forum1)
        self.forum3 = Forum.objects.create(name='Forum 3', parent=self.forum1)

        forums = [self.forum1, self.forum2, self.forum3]

        for f in forums:
            Privilege.objects.create(user=self.admin, forum=f,
                    positive=self.privileges, negative=0)

        self.topic = Topic.objects.create(title='A test Topic', author=self.user,
                forum=self.forum2)
        self.post = Post.objects.create(text=u'Post 1', author=self.user,
                topic=self.topic)

        self.client.defaults['HTTP_HOST'] = 'forum.%s' % settings.BASE_DOMAIN_NAME
        self.client.login(username='admin', password='admin')

    def _setup_pagination(self):
        """ Create enough topics for pagination test """
        def newtopic():
            t = Topic.objects.create(title="Title %s" % randint(1, 100000),
                                     author=self.user, forum=self.forum3)
            p = Post.objects.create(topic=t, text="Post %s" % randint(1, 100000),
                                    author=self.user, position=0)
            t.first_post_id = p.id
            t.save()
            for i in xrange(1, randint(2, 3)):
                Post.objects.create(text="More Posts %s" % randint(1, 100000),
                                    topic=t, author=self.user, position=i)
            for i in xrange(1, randint(2, 3)):
                Post.objects.create(text="More Posts %s" % randint(1, 100000),
                                    topic=t, author=self.admin, position=i)
        self.num_topics_on_last_page = int(round(TOPICS_PER_PAGE * 0.66))
        for _ in xrange(1, 4 * TOPICS_PER_PAGE + self.num_topics_on_last_page):
            newtopic()

    def test_reported_topics(self):
        response = self.client.get('/reported_topics/')
        self.assertEqual(response.status_code, 200)

    @patch('inyoka.middlewares.security.SecurityMiddleware._make_token',
            return_value='csrf_key')
    @patch('inyoka.forum.views.send_notification')
    def test_movetopic(self, mock_send, mock_security):
        self.assertEqual(Topic.objects.get(id=self.topic.id).forum_id,
                self.forum2.id)
        response = self.client.post('/topic/%s/move/' % self.topic.slug,
                    {'_form_token': 'csrf_key', 'forum': self.forum3.id})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(mock_send.call_count, 1) #only the topic author
        mock_send.assert_called_with(self.user, 'topic_moved',
            u'Your topic “A test Topic“ was moved.', {
                'username': self.user.username, 'topic': self.topic,
                'mod': self.admin.username, 'forum_name': 'Forum 3',
                'old_forum_name': 'Forum 2'})

        self.assertEqual(Topic.objects.get(id=self.topic.id).forum_id,
                self.forum3.id)

    def test_subscribe(self):
        self.client.login(username='user', password='user')
        useraccess = Privilege.objects.create(user=self.user, forum=self.forum2,
            positive=PRIVILEGES_BITS['read'], negative=0)

        self.client.get('/topic/%s/subscribe/' % self.topic.slug)
        self.assertTrue(
                   Subscription.objects.user_subscribed(self.user, self.topic))

        # Test for unsubscribe-link in the usercp if the user has no more read 
        # access to a subscription
        useraccess.positive = 0
        useraccess.save()
        response = self.client.get('/usercp/subscriptions/', {}, False,
                         HTTP_HOST='portal.%s' % settings.BASE_DOMAIN_NAME)
        self.assertTrue(('/topic/%s/unsubscribe/?next=' % self.topic.slug)
                         in response.content.decode("utf-8"))

        forward_url = 'http://portal.%s/myfwd' % settings.BASE_DOMAIN_NAME
        response = self.client.get('/topic/%s/unsubscribe/' % self.topic.slug,
                                    { 'next': forward_url })
        self.assertFalse(
                   Subscription.objects.user_subscribed(self.user, self.topic))
        self.assertEqual(response['location'], forward_url)

    def test_continue(self):
        """ The Parameter continue was renamed into next """

        urls = ["/",
                "/forum/%s/" % self.forum2.slug,
                "/topic/%s/" % self.topic.slug]
        for url in urls:
            response = self.client.get(url)
            self.assertFalse('?continue=' in response.content.decode("utf-8"))

    @override_settings(PROPAGATE_TEMPLATE_CONTEXT=True)
    def test_topiclist(self):
        self._setup_pagination()
        self.assertEqual(len(self.client.get("/last24/").tmpl_context['topics']),
                         TOPICS_PER_PAGE)
        self.assertEqual(len(self.client.get("/last24/3/").tmpl_context['topics']),
                         TOPICS_PER_PAGE)
        self.assertEqual(len(self.client.get("/last24/5/").tmpl_context['topics']),
                         self.num_topics_on_last_page)
        self.assertTrue(self.client.get("/last24/6/").status_code == 404)

        action_paginationurl = [
            href('forum', 'last%d' % 24, self.forum3.slug),
            href('forum', 'last%d' % 24),
            href('forum', 'egosearch', self.forum3.slug),
            href('forum', 'egosearch'),
            href('forum', 'author', self.user.username, self.forum3.slug),
            href('forum', 'author', self.user.username),
            href('forum', 'unsolved', self.forum3.slug),
            href('forum', 'unsolved'),
            href('forum', 'topic_author', self.user.username, self.forum3.slug),
            href('forum', 'topic_author', self.user.username),
            href('forum', 'newposts', self.forum3.slug),
            href('forum', 'newposts')]

        for url in action_paginationurl:
            # InyokaClient.get needs only the right part of the url
            path = url[url.index(settings.BASE_DOMAIN_NAME) +
                      len(settings.BASE_DOMAIN_NAME):]
            response = self.client.get(path)
            self.assertIn('%s2/' % url, response.tmpl_context['pagination'],
                    "%s does not render pagination urls properly" % path)
            self.assertNotIn('%s6/' % url, response.tmpl_context['pagination'],
                    "%s does display more pages than available" % path)

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
        self.assertEqual(response.status_code, 200) # was 302 before

        response = self.client.get('/', {
                    '__service__': 'forum.mark_topic_split_point',
                    'post': p2.pk,
                    'topic': t2.slug})
        response = self.client.get('/topic/%s/split/' % t2.slug)
        self.assertEqual(response.status_code, 200)

    @patch('inyoka.middlewares.security.SecurityMiddleware._make_token',
            return_value='csrf_key')
    def test_add_attachment(self, mock_send):
        # Version Choices not available in Tests
        constants.VERSION_CHOICES = [(u'', u'None'),
                                     (u'natty', u'Natty'),
                                     (u'hardy', u'Hardy')]
        VERSION_CHOICES = constants.VERSION_CHOICES
        TEST_ATTACHMENT = 'test_attachment.png'

        t1 = Topic.objects.create(title='A: topic', slug='a:-topic',
                author=self.user, forum=self.forum2,
                ubuntu_version=VERSION_CHOICES[1][0],
                ubuntu_distro=DISTRO_CHOICES[1][0])
        p1 = Post.objects.create(text=u'Post 1', author=self.user,
                topic=t1)

        f = open(path.join(path.dirname(__file__), TEST_ATTACHMENT), 'rb')
        postdata = {u'attachment': f,
                    u'attach' : u'upload attachment',
                    u'ubuntu_distro': DISTRO_CHOICES[2][0],
                    u'ubuntu_version': VERSION_CHOICES[2][0],
                    u'comment': u'',
                    u'attachments': u'',
                    u'title': u'Tag124345637',
                    u'text': u'Tag23562434',
                    u'polls': u'',
                    u'question': u'',
                    u'filename': u'',
                    u'duration': u'',
                    u'options': u'',
                    u'_form_token': u'csrf_key' }


        response = self.client.post('/post/%s/edit/' % p1.pk, postdata)
        content = unicode(response.__str__().decode(response._charset))

        self.assertIn(postdata['title'], content)
        self.assertIn(postdata['text'], content)
        self.assertIn(u'value="%s" selected="selected"' % DISTRO_CHOICES[2][0],
                      content)
        self.assertIn(u'value="%s" selected="selected"' % VERSION_CHOICES[2][0],
                      content)
        self.assertIn(unicode(TEST_ATTACHMENT), content)

        # Adding an attachment should not trigger save
        t1_test = Topic.objects.get(pk=t1.pk)
        self.assertEqual(t1_test.title, u'A: topic')
        self.assertEqual(t1_test.ubuntu_version, VERSION_CHOICES[1][0])
        self.assertEqual(t1_test.ubuntu_distro, DISTRO_CHOICES[1][0])

        p1_test = Post.objects.get(pk=p1.pk)
        self.assertEqual(p1_test.text, u'Post 1')
