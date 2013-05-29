#-*- coding: utf-8 -*-
from datetime import datetime

from django.conf import settings
from django.test import TestCase
from django.utils import translation

from inyoka.portal.user import User, PERMISSION_NAMES
from inyoka.planet.models import Blog, Entry
from inyoka.utils.test import InyokaClient


class TestViews(TestCase):

    client_class = InyokaClient
    permissions = sum(PERMISSION_NAMES.keys())

    def setUp(self):
        self.admin = User.objects.register_user('admin', 'admin', 'admin', False)
        self.admin._permissions = self.permissions
        self.admin.save()

        self.client.defaults['HTTP_HOST'] = 'planet.%s' % settings.BASE_DOMAIN_NAME
        self.client.login(username='admin', password='admin')

    def test_empty_post_title(self):
        blog = Blog(name="Testblog", blog_url="http://example.com/",
                    feed_url="http://example.com/feed", user=self.admin,
                    active=True)
        blog.save()
        Entry.objects.create(blog=blog, url="http://example.com/article1",
                             guid="http://example.com/article1",
                             text="This is a test", title="",
                             pub_date=datetime.now(), updated=datetime.now())
        Entry.objects.create(blog=blog, url="http://example.com/article2",
                             guid="http://example.com/article2",
                             text="This is a test", title="I have a title",
                             pub_date=datetime.now(), updated=datetime.now())

        with translation.override('en-us'):
            response = self.client.post('/feeds/title/10/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No title given", count=1)

        with translation.override('en-us'):
            response = self.client.post('/feeds/short/10/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No title given", count=1)

        with translation.override('en-us'):
            response = self.client.post('/feeds/full/10/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No title given", count=1)

