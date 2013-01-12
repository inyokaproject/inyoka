#-*- coding: utf-8 -*-
"""
    tests.functional.apps.ikhaya.test_models
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test Ikhaya models.

    :copyright: (c) 2011-2013 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL.
"""
from django.test import TestCase

from datetime import date, time

from inyoka.ikhaya.models import Article, Category
from inyoka.portal.user import User


class TestArticleModel(TestCase):

    def setUp(self):
        self.user = User.objects.register_user('admin', 'admin', 'admin',
                False)

        self.category1 = Category(name='Test Category 1')
        self.category1.save()
        self.category2 = Category(name='Test Category 2')
        self.category2.save()

        self.article1 = Article(pub_date=date(2008, 7, 18), text='Text 1',
                pub_time=time(1, 33, 7), author=self.user, subject='Article 1',
                category=self.category1, intro='Intro 1')
        self.article1.save()

        self.article2 = Article(pub_date=date(2008, 7, 18), text="'''Text 2'''",
                pub_time=time(0, 0, 0), author=self.user, subject='Article 2',
                category=self.category2, intro='Intro 2')
        self.article2.save()

        self.article3 = Article(pub_date=date(2009, 4, 1), text='<a>Text 3</a>',
                pub_time=time(12, 34, 56), author=self.user,
                subject='Article 3', category=self.category1, intro='Intro 3',
                is_xhtml=True)
        self.article3.save()

    def test_automatic_slugs(self):
        self.assertEqual(self.category1.slug, 'test-category')

        self.assertEqual(self.category2.slug, 'test-category-2')

        self.assertEqual(self.article1.slug, 'article')
        self.assertEqual(self.article1.stamp, '2008/07/18')

        self.assertEqual(self.article2.slug, 'article-2')
        self.assertEqual(self.article2.stamp, '2008/07/18')

        self.assertEqual(self.article3.slug, 'article')
        self.assertEqual(self.article3.stamp, '2009/04/01')

    def test_simplify_xhtml(self):
        self.assertEqual(self.article3.simplified_text, 'Text 3')

    def test_simplify_wiki_markup(self):
        self.assertEqual(self.article2.simplified_text, 'Text 2')

    def test_simplify_does_strip(self):
        _old_text = self.article1.text
        self.article1.text = 'Text 1   '
        self.assertEqual(self.article1.simplified_text, 'Text 1')
        self.article1.text = _old_text