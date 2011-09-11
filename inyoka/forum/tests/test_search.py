#-*- coding: utf-8 -*-
import time
from datetime import datetime
from inyoka.testing import SearchTestCase
from pyes.exceptions import ElasticSearchException
from inyoka.forum.models import Forum, Topic, Post
from inyoka.portal.user import User


class ForumSearchTest(SearchTestCase):
    fixtures = ['base.json']

    def test_ikhaya_index(self):
        forum = Forum.objects.get(slug='test-sub')
        admin = User.objects.get('admin')
        topic = Topic(title='Fancy!', author=admin, forum=forum)
        topic.save()
        post = Post(topic=topic, text=u'More Fancy!', author=admin,
                    pub_date=datetime.utcnow(), position=0)
        post.save()
        self.search.store('forum', 'post', post)
        time.sleep(1)
        results = self.search.search('More Fancy')
        self.assertEqual('test-sub', results.hits[0].source.forum_slug)
