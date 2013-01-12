#-*- coding: utf-8 -*-
"""
    tests.functional.apps.ikhaya.test_views
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test Ikhaya views.

    :copyright: (c) 2012-2013 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL.
"""
from datetime import datetime

from django.conf import settings
from django.test import TestCase

from inyoka.ikhaya.models import Article, Category, Comment, Report
from inyoka.portal.user import User, PERMISSION_NAMES
from inyoka.utils.test import InyokaClient


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
                            text="Text", pub_date=datetime.today().date(),
                            pub_time=datetime.now().time(), category=self.cat)
        self.comment = Comment.objects.create(article=self.article, text="Text",
                            author=self.user, pub_date=datetime.now())
        self.report = Report.objects.create(article=self.article, text="Text",
                            author=self.user, pub_date=datetime.now())

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
