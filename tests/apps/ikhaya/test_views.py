#-*- coding: utf-8 -*-
"""
    tests.apps.ikhaya.test_views
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test Ikhaya views.

    :copyright: (c) 2012-2015 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import datetime

from django.conf import settings
from django.test import TestCase

from inyoka.utils.test import InyokaClient
from inyoka.utils.urls import href
from inyoka.portal.user import User, PERMISSION_NAMES
from inyoka.ikhaya.models import Report, Article, Comment, Category


class TestViews(TestCase):

    client_class = InyokaClient
    permissions = sum(PERMISSION_NAMES.keys())

    def setUp(self):
        self.admin = User.objects.register_user('admin', 'admin', 'admin', False)
        self.user = User.objects.register_user('user', 'user', 'user', False)
        self.admin._permissions = self.permissions
        self.admin.save()

        self.cat = Category.objects.create(name="Categrory")
        self.article = Article.objects.create(author=self.admin, subject="Subject",
                            text="Text", pub_date=datetime.datetime.today().date(),
                            pub_time=datetime.datetime.now().time(), category=self.cat)
        self.comment = Comment.objects.create(article=self.article, text="Text",
                            author=self.user, pub_date=datetime.datetime.now())
        self.report = Report.objects.create(article=self.article, text="Text",
                            author=self.user, pub_date=datetime.datetime.now())

        self.client.defaults['HTTP_HOST'] = 'ikhaya.%s' % settings.BASE_DOMAIN_NAME
        self.client.login(username='admin', password='admin')

    def test_comment_update(self):
        self.assertEqual(Comment.objects.get(id=self.comment.id).deleted, False)

        self.client.post('/comment/%d/hide/' % self.comment.id, {'cancel': True})
        self.assertEqual(Comment.objects.get(id=self.comment.id).deleted, False)

        self.client.post('/comment/%d/hide/' % self.comment.id, {'confirm': True})
        self.assertEqual(Comment.objects.get(id=self.comment.id).deleted, True)

        self.client.post('/comment/%d/restore/' % self.comment.id, {'cancel': True})
        self.assertEqual(Comment.objects.get(id=self.comment.id).deleted, True)

        self.client.post('/comment/%d/restore/' % self.comment.id, {'confirm': True})
        self.assertEqual(Comment.objects.get(id=self.comment.id).deleted, False)

    def test_report_deleted_update(self):
        self.assertEqual(Report.objects.get(id=self.report.id).deleted, False)

        self.client.post('/report/%d/hide/' % self.report.id, {'cancel': True})
        self.assertEqual(Report.objects.get(id=self.report.id).deleted, False)

        self.client.post('/report/%d/hide/' % self.report.id, {'confirm': True})
        self.assertEqual(Report.objects.get(id=self.report.id).deleted, True)

        self.client.post('/report/%d/restore/' % self.report.id, {'cancel': True})
        self.assertEqual(Report.objects.get(id=self.report.id).deleted, True)

        self.client.post('/report/%d/restore/' % self.report.id, {'confirm': True})
        self.assertEqual(Report.objects.get(id=self.report.id).deleted, False)

    def test_report_solved_update(self):
        self.assertEqual(Report.objects.get(id=self.report.id).solved, False)

        self.client.post('/report/%d/solve/' % self.report.id, {'cancel': True})
        self.assertEqual(Report.objects.get(id=self.report.id).solved, False)

        self.client.post('/report/%d/solve/' % self.report.id, {'confirm': True})
        self.assertEqual(Report.objects.get(id=self.report.id).solved, True)

        self.client.post('/report/%d/unsolve/' % self.report.id, {'cancel': True})
        self.assertEqual(Report.objects.get(id=self.report.id).solved, True)

        self.client.post('/report/%d/unsolve/' % self.report.id, {'confirm': True})
        self.assertEqual(Report.objects.get(id=self.report.id).solved, False)

    def test_ticket_854(self):
        user_w = User.objects.register_user('user_w', 'user_w', 'user', False)
        user_w.avatar = "test/path/to/avatarimage.png"
        user_w.save()

        user_wo = User.objects.register_user('user_wo', 'user_wo', 'user', False)

        user_g = User.objects.register_user('user_g', 'user_g', 'user', False)
        user_g.settings['use_gravatar'] = True
        user_g.save()

        avatar_url = href('media', user_w.avatar)
        gravatar_url = 'http://www.gravatar.com/avatar/ca39ffdca4bd97c3a6c29a4c8f29b7dc?s=80&amp;r=g&amp;d=mm'

        a = Article.objects.create(author=self.admin, subject="Subject 2",
                            text="Text 3", pub_date=datetime.datetime.today().date(),
                            pub_time=datetime.datetime.now().time(), category=self.cat)
        for u in (user_w, user_wo, user_g):
            Comment.objects.create(article=a, text="Comment by %s" % u.username,
                            author=u, pub_date=datetime.datetime.now())

        response = self.client.get("/%s/%s" % (a.stamp, a.slug), follow=True)
        self.assertContains(response, avatar_url, count=1)
        self.assertContains(response, '''<td class="author">
            <p class="username">
                <a href="%s">user wo</a>
            </p>
        </td>''' % user_wo.get_absolute_url(action='show'), count=1, html=True)
        self.assertContains(response, gravatar_url, count=1)
        self.assertContains(response, '<td class="author">', count=3)

    def test_add_event_without_data(self):
        response = self.client.post('/event/suggest/', {'confirm': True})
        self.assertContains(response, 'date<ul class="errorlist">', 1)
        self.assertContains(response, 'name<ul class="errorlist">', 1)
        self.assertContains(response, 'errorlist', 3)

    def test_add_event_without_name(self):
        response = self.client.post('/event/suggest/', {'date': datetime.date(2015, 5, 1),
                                                        'enddate': datetime.date(2015, 5, 2),
                                                        'confirm': True})
        self.assertContains(response, 'name<ul class="errorlist"', 1)
        self.assertContains(response, 'errorlist', 2)

    def test_add_event_with_name_startdate_enddate(self):
        response = self.client.post('/event/suggest/', {'date': datetime.date(2015, 5, 1),
                                                        'enddate': datetime.date(2015, 5, 2),
                                                        'name': 'TestEvent',
                                                        'confirm': True})
        self.assertEquals(response.status_code, 302)

    def test_add_event_with_name_enddate_before_startdate(self):
        response = self.client.post('/event/suggest/', {'date': datetime.date(2015, 6, 1),
                                                        'enddate': datetime.date(2015, 5, 2),
                                                        'name': 'TestEvent',
                                                        'confirm': True})
        self.assertContains(response, 'enddate<ul class="errorlist">', 1)
        self.assertContains(response, 'errorlist', 2)

    def test_add_event_with_name_and_startdate(self):
        response = self.client.post('/event/suggest/', {'date': datetime.date(2015, 6, 1),
                                                        'name': 'TestEvent',
                                                        'confirm': True})
        self.assertEquals(response.status_code, 302)

    def test_add_event_with_name_startdatetime_enddatetime_midnight(self):
        response = self.client.post('/event/suggest/', {'date': datetime.date(2015, 5, 1),
                                                        'time': datetime.time(0, 0, 0),
                                                        'enddate': datetime.date(2015, 5, 2),
                                                        'endtime': datetime.time(0, 0, 0),
                                                        'name': 'TestEvent',
                                                        'confirm': True})
        self.assertEquals(response.status_code, 302)

    def test_add_event_with_name_startdatetime_enddatetime(self):
        response = self.client.post('/event/suggest/', {'date': datetime.date(2015, 5, 1),
                                                        'time': datetime.time(10, 0, 0),
                                                        'enddate': datetime.date(2015, 5, 2),
                                                        'endtime': datetime.time(11, 0, 0),
                                                        'name': 'TestEvent',
                                                        'confirm': True})
        self.assertEquals(response.status_code, 302)

    def test_add_event_with_name_enddatetime_before_startdatetime(self):
        response = self.client.post('/event/suggest/', {'date': datetime.date(2015, 5, 1),
                                                        'time': datetime.time(10, 0, 0),
                                                        'enddate': datetime.date(2015, 5, 1),
                                                        'endtime': datetime.time(9, 0, 0),
                                                        'name': 'TestEvent',
                                                        'confirm': True})
        self.assertContains(response, 'endtime<ul class="errorlist">', 1)
        self.assertContains(response, 'errorlist', 2)

    def test_add_event_with_name_startdatetime_enddatetime(self):
        response = self.client.post('/event/suggest/', {'date': datetime.date(2015, 4, 30),
                                                        'time': datetime.time(23, 0, 0),
                                                        'enddate': datetime.date(2015, 5, 1),
                                                        'endtime': datetime.time(9, 0, 0),
                                                        'name': 'TestEvent',
                                                        'confirm': True})
        self.assertEquals(response.status_code, 302)
