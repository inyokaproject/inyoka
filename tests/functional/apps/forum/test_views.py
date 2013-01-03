#-*- coding: utf-8 -*-
from mock import patch
from random import randint
from os import path

from django.conf import settings
from django.test import TestCase, Client
from django.test.utils import override_settings
from django.utils.translation import ugettext as _

from inyoka.forum.acl import PRIVILEGES_BITS
from inyoka.forum.constants import TOPICS_PER_PAGE, DISTRO_CHOICES
from inyoka.forum.models import Forum, Topic, Post, Privilege
from inyoka.portal.user import User, PERMISSION_NAMES
from inyoka.portal.models import Subscription
from inyoka.utils.test import InyokaClient
from inyoka.utils.urls import href


class TestForumViews(TestCase):

    @override_settings(BASE_DOMAIN_NAME='inyoka.local')
    def test_forum_index(self):
        client = Client(HTTP_HOST='forum.inyoka.local')
        resp = client.get('/')
        self.assertEqual(resp.status_code, 200)


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
                posts.append(Post(text="More Posts %s" % randint(1, 100000),
                                    topic=t, author=self.user, position=i))
            for i in xrange(1, randint(2, 3)):
                posts.append(Post(text="More Posts %s" % randint(1, 100000),
                                    topic=t, author=self.admin, position=i))

        self.num_topics_on_last_page = int(round(TOPICS_PER_PAGE * 0.66))
        for i in xrange(1, 4 * TOPICS_PER_PAGE + self.num_topics_on_last_page):
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
                                    {'next': forward_url})
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
            urlpath = url[url.index(settings.BASE_DOMAIN_NAME) +
                      len(settings.BASE_DOMAIN_NAME):]
            response = self.client.get(urlpath)
            self.assertIn('%s2/' % url, response.tmpl_context['pagination'],
                    "%s does not render pagination urls properly" % urlpath)
            self.assertNotIn('%s6/' % url, response.tmpl_context['pagination'],
                    "%s does display more pages than available" % urlpath)

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
                return list(Post.objects.filter(topic_id=topicid)\
                    .values_list(*field).order_by('position'))
            else:
                return list(Post.objects.filter(topic_id=topicid)\
                    .values_list(field, flat=True).order_by('position'))

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

    def test_add_attachment(self):
        TEST_ATTACHMENT = 'test_attachment.png'

        t1 = Topic.objects.create(title='A: topic', slug='a:-topic',
                author=self.user, forum=self.forum2,
                ubuntu_distro=DISTRO_CHOICES[1][0])
        p1 = Post.objects.create(text=u'Post 1', author=self.user,
                topic=t1)

        f = open(path.join(path.dirname(__file__), TEST_ATTACHMENT), 'rb')
        postdata = {u'attachment': f,
                    u'attach': u'upload attachment',
                    u'ubuntu_distro': DISTRO_CHOICES[2][0],
                    u'comment': u'',
                    u'attachments': u'',
                    u'title': u'Tag124345637',
                    u'text': u'Tag23562434',
                    u'polls': u'',
                    u'question': u'',
                    u'filename': u'',
                    u'duration': u'',
                    u'options': u''}

        response = self.client.post('/post/%s/edit/' % p1.pk, postdata)
        content = unicode(response.__str__().decode(response._charset))

        self.assertIn(postdata['title'], content)
        self.assertIn(postdata['text'], content)
        self.assertIn(u'value="%s" selected="selected"' % DISTRO_CHOICES[2][0],
                      content)
        self.assertIn(unicode(TEST_ATTACHMENT), content)

        # Adding an attachment should not trigger save
        t1_test = Topic.objects.get(pk=t1.pk)
        self.assertEqual(t1_test.title, u'A: topic')
        self.assertEqual(t1_test.ubuntu_distro, DISTRO_CHOICES[1][0])

        p1_test = Post.objects.get(pk=p1.pk)
        self.assertEqual(p1_test.text, u'Post 1')
