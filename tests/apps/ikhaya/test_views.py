"""
    tests.apps.ikhaya.test_views
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test Ikhaya views.

    :copyright: (c) 2012-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import datetime
import zoneinfo
from unittest.mock import patch

import feedparser
from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.core import mail
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory
from django.utils import timezone as dj_timezone
from django.utils.dateparse import parse_datetime
from freezegun import freeze_time
from guardian.shortcuts import assign_perm, remove_perm

from inyoka.ikhaya.models import Article, Category, Comment, Event, Report, Suggestion
from inyoka.ikhaya.views import detail, event_delete, event_edit, events, index
from inyoka.portal.models import PrivateMessage, PrivateMessageEntry, Subscription
from inyoka.portal.user import User
from inyoka.utils.storage import storage
from inyoka.utils.test import InyokaClient, TestCase
from inyoka.utils.urls import href


class TestViews(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()
        self.admin = User.objects.register_user('admin', 'admin', 'admin', False)
        self.user = User.objects.register_user('user', 'user', 'user', False)
        self.admin.is_superuser = True
        self.admin.save()

        self.cat = Category.objects.create(name="Categrory")
        self.article = Article.objects.create(author=self.admin, subject="Subject",
                            text="Text", pub_date=datetime.datetime.today().date(),
                            pub_time=datetime.datetime.now().time(), category=self.cat)
        self.comment = Comment.objects.create(article=self.article, text="Text",
                            author=self.user, pub_date=dj_timezone.now())
        self.report = Report.objects.create(article=self.article, text="Text",
                            author=self.user, pub_date=dj_timezone.now())

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
        gravatar_url_part = 'https://www.gravatar.com/avatar/ca39ffdca4bd97c3a6c29a4c8f29b7dc'

        a = Article.objects.create(author=self.admin, subject="Subject 2",
                            text="Text 3", pub_date=datetime.datetime.today().date(),
                            pub_time=datetime.datetime.now().time(), category=self.cat)
        for u in (user_w, user_wo, user_g):
            Comment.objects.create(article=a, text="Comment by %s" % u.username,
                            author=u, pub_date=dj_timezone.now())

        response = self.client.get("/%s/%s" % (a.stamp, a.slug), follow=True)
        self.assertContains(response, avatar_url, count=1)
        self.assertContains(response, '''<td class="author">
            <p class="username">
                <a href="%s">user_wo</a>
            </p>
        </td>''' % user_wo.get_absolute_url(action='show'), count=1, html=True)
        self.assertContains(response, gravatar_url_part, count=1)
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
        self.assertEqual(response.status_code, 302)

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
        self.assertEqual(response.status_code, 302)

    def test_add_event_with_name_startdatetime_enddatetime_midnight(self):
        response = self.client.post('/event/suggest/', {'date': datetime.date(2015, 5, 1),
                                                        'time': datetime.time(0, 0, 0),
                                                        'enddate': datetime.date(2015, 5, 2),
                                                        'endtime': datetime.time(0, 0, 0),
                                                        'name': 'TestEvent',
                                                        'confirm': True})
        self.assertEqual(response.status_code, 302)

    def test_add_event_with_name_startdatetime_enddatetime(self):
        response = self.client.post('/event/suggest/', {'date': datetime.date(2015, 5, 1),
                                                        'time': datetime.time(10, 0, 0),
                                                        'enddate': datetime.date(2015, 5, 2),
                                                        'endtime': datetime.time(11, 0, 0),
                                                        'name': 'TestEvent',
                                                        'confirm': True})
        self.assertEqual(response.status_code, 302)

    def test_add_event_with_name_enddatetime_before_startdatetime(self):
        response = self.client.post('/event/suggest/', {'date': datetime.date(2015, 5, 1),
                                                        'time': datetime.time(10, 0, 0),
                                                        'enddate': datetime.date(2015, 5, 1),
                                                        'endtime': datetime.time(9, 0, 0),
                                                        'name': 'TestEvent',
                                                        'confirm': True})
        self.assertContains(response, 'endtime<ul class="errorlist">', 1)
        self.assertContains(response, 'errorlist', 2)


class TestIndex(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()
        self.admin = User.objects.register_user('admin', 'admin', 'admin', False)
        self.admin.is_superuser = True
        self.admin.save()

        self.user = User.objects.register_user('user', 'user', 'user', False)

        self.cat = Category.objects.create(name="Categrory")
        self.article = Article.objects.create(author=self.admin, subject="a1Subject",
                                              intro="a1Intro", text="a1Text",
                                              pub_date=datetime.datetime.today().date(),
                                              pub_time=datetime.datetime.now().time(),
                                              category=self.cat)

        self.client.defaults['HTTP_HOST'] = 'ikhaya.%s' % settings.BASE_DOMAIN_NAME
        self.client.login(username='admin', password='admin')

    def test_status_code(self):
        response = self.client.get('')
        self.assertEqual(response.status_code, 200)

    def test_month(self):
        article2 = Article.objects.create(author=self.admin, subject="a2Subject",
                                              intro="a2Intro", text="a2Text",
                                              pub_date=datetime.date(2005, 2, 10),
                                              pub_time=datetime.time(12, 0),
                                              category=self.cat)

        response = self.client.get('/2005/2/')
        self.assertContains(response, article2.subject)
        self.assertNotContains(response, self.article.subject)

    def test_category(self):
        cat2 = Category.objects.create(name="Categrory2")
        article2 = Article.objects.create(author=self.admin, subject="a2Subject",
                                              intro="a2Intro", text="a2Text",
                                              pub_date=datetime.datetime.today().date(),
                                              pub_time=datetime.datetime.now().time(),
                                              category=cat2)

        response = self.client.get(f'/category/{self.cat.slug}/')
        self.assertContains(response, self.article.subject)
        self.assertNotContains(response, article2.subject)

    def test_second_page(self):
        for i in range(2, 20):
            Article.objects.create(author=self.admin, subject=f"a{i}Subject",
                               intro=f"a{i}Intro", text=f"a{i}Text",
                               pub_date=datetime.date(2005, 2, i),
                               pub_time=datetime.time(12, 0),
                               category=self.cat)

        article_last = Article.objects.create(author=self.admin, subject="aLastSubject",
                               intro="aLastIntro", text="aLastText",
                               pub_date=datetime.date(2004, 5, 1),
                               pub_time=datetime.time(13, 0),
                               category=self.cat)

        response = self.client.get('/2/')
        self.assertContains(response, article_last.subject)
        self.assertNotContains(response, self.article.subject)

        response = self.client.get(f'/category/{article_last.category.slug}/2/')
        self.assertContains(response, article_last.subject)
        self.assertNotContains(response, self.article.subject)

    def test_pagination__with_year_month(self):
        response = self.client.get(f'/{self.article.local_pub_datetime.year}/{self.article.local_pub_datetime.month}/1/')
        self.assertContains(response, self.article.subject)

    def test_article_content(self):
        response = self.client.get('')
        self.assertContains(response, self.article.subject)
        self.assertContains(response, self.article.intro)
        self.assertNotContains(response, self.article.text)

    def test_full_article_content(self):
        urls = ('/full/',
                '/full/1/',
                f'/{self.article.local_pub_datetime.year}/{self.article.local_pub_datetime.month}/full/',
                f'/category/{self.article.category.slug}/full/',
                f'/category/{self.article.category.slug}/full/1/',
                f'/{self.article.local_pub_datetime.year}/{self.article.local_pub_datetime.month}/full/1/',
                )

        for u in urls:
            with self.subTest(url=u):
                response = self.client.get(u)
                self.assertContains(response, self.article.text, count=1, html=True)

    def test_anonymous_user__no_unpublished_articles(self):
        article_public = Article.objects.create(author=self.admin, subject="a2Subject",
                                          intro="a2Intro", text="a2Text",
                                          pub_date=datetime.date(2005, 2, 10),
                                          pub_time=datetime.time(12, 0),
                                          category=self.cat,
                                          public=True)

        factory = RequestFactory()
        request = factory.get('/')
        request.user = User.objects.get_anonymous_user()
        response = index(request)
        self.assertContains(response, article_public.subject)
        self.assertNotContains(response, self.article.subject)

    def test_order_of_articles(self):
        old_public = Article.objects.create(author=self.admin, subject="a2Subject",
                                                intro="a2Intro", text="a2Text",
                                                pub_date=datetime.date(2005, 2, 10),
                                                pub_time=datetime.time(12, 0),
                                                category=self.cat,
                                                public=True)

        public = Article.objects.create(author=self.admin, subject="aPublicSubject",
                                          intro="aPublicIntro", text="aPublicText",
                                          pub_date=datetime.date(2024, 2, 10),
                                          pub_time=datetime.time(10, 0),
                                          category=self.cat,
                                          public=True)

        public_same_day = Article.objects.create(author=self.admin, subject="aPublic2Subject",
                                          intro="aPublic2Intro", text="aPublic2Text",
                                          pub_date=datetime.date(2024, 2, 10),
                                          pub_time=datetime.time(20, 0),
                                          category=self.cat,
                                          public=True)

        updated = Article.objects.create(author=self.admin, subject="aUpdateSubject",
                                         intro="aUpdateIntro", text="aUpdateText",
                                         pub_date=datetime.date(2023, 2, 10),
                                         pub_time=datetime.time(10, 0),
                                         updated = datetime.datetime(2024, 2, 11, 21, 0),
                                         category=self.cat,
                                         public=True)

        old_draft = Article.objects.create(author=self.admin, subject="aOldDraftSubject",
                                                intro="aOldDraftIntro", text="aOldDraftText",
                                                pub_date=datetime.date(2005, 2, 10),
                                                pub_time=datetime.time(20, 0),
                                                category=self.cat,
                                                public=False)

        response = self.client.get('')
        self.assertListEqual(response.context['articles'],
                              [self.article, old_draft, updated, public_same_day, public, old_public])


class TestArticleDetail(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()
        self.admin = User.objects.register_user('admin', 'admin', 'admin', False)
        self.admin.is_superuser = True
        self.admin.save()

        self.user = User.objects.register_user('user', 'user', 'user', False)

        self.cat = Category.objects.create(name="Categrory")
        self.article = Article.objects.create(author=self.admin, subject="a1Subject",
                                              intro="a1Intro", text="a1Text",
                                              pub_date=datetime.datetime.today().date(),
                                              pub_time=datetime.datetime.now().time(),
                                              category=self.cat)

        self.client.defaults['HTTP_HOST'] = 'ikhaya.%s' % settings.BASE_DOMAIN_NAME
        self.client.login(username='admin', password='admin')

    def test_status_code(self):
        response = self.client.get(f'/{self.article.stamp}/{self.article.slug}/')
        self.assertEqual(response.status_code, 200)

    def test_not_existing_article_status_code(self):
        response = self.client.get('/1785/5/8/goo/')
        self.assertEqual(response.status_code, 404)

    def test_user_views_unpublished_article(self):
        self.client.login(username='user', password='user')

        response = self.client.get(f'/{self.article.stamp}/{self.article.slug}/')
        self.assertEqual(response.status_code, 403)

    def test_anonymous_user_http_post_not_allowed(self):
        factory = RequestFactory()
        request = factory.post(f'/{self.article.stamp}/{self.article.slug}/', {})
        request.user = User.objects.get_anonymous_user()
        with self.assertRaises(PermissionDenied):
            detail(request,
                   self.article.local_pub_datetime.year,
                   self.article.local_pub_datetime.month,
                   self.article.local_pub_datetime.day,
                   self.article.slug,
                   )

    def test_comments_disabled__no_http_post_possible(self):
        self.article.comments_enabled = False
        self.article.save()

        response = self.client.post(f'/{self.article.stamp}/{self.article.slug}/', {})
        self.assertEqual(response.status_code, 403)

    def test_preview_rendered(self):
        canary_text = 'canary6718'

        response = self.client.post(f'/{self.article.stamp}/{self.article.slug}/', {'preview': True, 'text': canary_text})
        self.assertContains(response, canary_text, count=2, html=True)

    def test_post_new_comment(self):
        response = self.client.post(f'/{self.article.stamp}/{self.article.slug}/',
                                    {'text': 'my great new text'}, follow=True)

        self.assertRedirects(response, f'http://ikhaya.{settings.BASE_DOMAIN_NAME}/{self.article.stamp}/a1subject/#comment_1')
        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(Comment.objects.get().text, 'my great new text')


class TestArticleDelete(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()
        self.admin = User.objects.register_user('admin', 'admin', 'admin', False)
        self.admin.is_superuser = True
        self.admin.save()

        self.user = User.objects.register_user('user', 'user', 'user', False)

        self.cat = Category.objects.create(name="Categrory")
        self.article = Article.objects.create(author=self.admin, subject="a1Subject",
                                              intro="a1Intro", text="a1Text",
                                              pub_date=datetime.datetime.today().date(),
                                              pub_time=datetime.datetime.now().time(),
                                              category=self.cat)

        self.client.defaults['HTTP_HOST'] = 'ikhaya.%s' % settings.BASE_DOMAIN_NAME
        self.client.login(username='admin', password='admin')

    def test_status_code(self):
        response = self.client.get(f'/{self.article.stamp}/{self.article.slug}/delete/', follow=True)
        self.assertEqual(response.status_code, 200)

    def test_not_existing_article__status_code(self):
        with self.assertRaises(Article.DoesNotExist):
            self.client.get('/1785/5/8/goo/delete/')

    def test_not_valid_month__status_code(self):
        response = self.client.get('/1785/a/8/goo/delete/')
        self.assertEqual(response.status_code, 404)

    def test_user___no_permission_http_403(self):
        self.client.login(username='user', password='user')

        response = self.client.get(f'/{self.article.stamp}/{self.article.slug}/delete/')
        self.assertEqual(response.status_code, 403)

    def test_unpublish(self):
        self.article.public = True
        self.article.save()

        self.client.post(f'/{self.article.stamp}/{self.article.slug}/delete/', data={'unpublish': True})

        self.article.refresh_from_db()
        self.assertFalse(self.article.public)

    def test_cancel(self):
        response = self.client.post(f'/{self.article.stamp}/{self.article.slug}/delete/', data={'cancel': True}, follow=True)
        self.assertContains(response, 'was canceled', count=1)

    def test_delete(self):
        self.client.post(f'/{self.article.stamp}/{self.article.slug}/delete/', data={})
        self.assertEqual(Article.objects.count(), 0)


class TestArticleEdit(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()
        self.admin = User.objects.register_user('admin', 'admin', 'admin', False)
        self.admin.is_superuser = True
        self.admin.save()

        self.user = User.objects.register_user('user', 'user', 'user', False)

        self.cat = Category.objects.create(name="Categrory")
        self.article = Article.objects.create(author=self.admin, subject="a1Subject",
                                              intro="a1Intro", text="a1Text",
                                              pub_date=datetime.datetime.today().date(),
                                              pub_time=datetime.datetime.now().time(),
                                              category=self.cat)

        self.client.defaults['HTTP_HOST'] = 'ikhaya.%s' % settings.BASE_DOMAIN_NAME
        self.client.login(username='admin', password='admin')

    def test_status_code(self):
        response = self.client.get(f'/{self.article.stamp}/{self.article.slug}/edit/', follow=True)
        self.assertEqual(response.status_code, 200)

    def test_not_existing_article__status_code(self):
        response = self.client.get('/1785/5/8/goo/edit/')
        self.assertEqual(response.status_code, 404)

    def test_not_valid_month__status_code(self):
        response = self.client.get('/1785/a/8/goo/edit/')
        self.assertEqual(response.status_code, 404)

    def test_lock(self):
        # request as admin
        self.client.get(f'/{self.article.stamp}/{self.article.slug}/edit/')

        # both admin and user should be able to edit articles
        self.user.is_superuser = True
        self.user.save()
        self.client.login(username='user', password='user')

        response = self.client.get(f'/{self.article.stamp}/{self.article.slug}/edit/')
        self.assertContains(response, 'edited by “admin”!', count=1)

    def test_suggestion__http_post(self):
        suggestion = Suggestion.objects.create(author=self.admin,
                                                    title='SugTitle',
                                                    intro='SugIntro',
                                                    text='SugText',
                                                    notes='SugNotes',
                                                    )

        data = {
            'author': self.admin.username,
            'subject': 'aNewSubject',
            'intro': 'aNewIntro',
            'text': 'aNewText',
            'pub_date': '2024-12-31',
            'pub_time': '23:55:00',
            'category': self.cat.pk,
            'send': True,
        }
        self.client.post(f'/article/new/{suggestion.id}/', data=data)

        self.assertEqual(Article.objects.count(), 2)
        self.assertEqual(Suggestion.objects.count(), 0)

    def test_suggestion__http_get(self):
        suggestion = Suggestion.objects.create(author=self.admin,
                                                    title='SugTitle',
                                                    intro='SugIntro',
                                                    text='SugText',
                                                    notes='SugNotes',
                                                    )
        response = self.client.get(f'/article/new/{suggestion.id}/')
        self.assertContains(response, suggestion.title, count=1)
        self.assertContains(response, suggestion.text, count=1)
        self.assertContains(response, suggestion.intro, count=1)

    def test_edit_article__not_public(self):
        data = {
            'author': self.admin.username,
            'subject': self.article.subject,
            'intro': 'aNewIntro',
            'text': 'aNewText',
            'pub_date': '2024-12-31',
            'pub_time': '23:55:00',
            'category': self.cat.pk,
            'send': True,
        }
        response = self.client.post(f'/{self.article.stamp}/{self.article.slug}/edit/',
                                    data=data,
                                    follow=True)
        self.assertContains(response, 'was saved', count=1)
        self.assertRedirects(response,
                             f'http://ikhaya.{settings.BASE_DOMAIN_NAME}/2024/12/31/{self.article.slug}/')

    def test_edit_article__not_public__slug_changed(self):
        data = {
            'author': self.admin.username,
            'subject': 'aNewSubject',
            'intro': 'aNewIntro',
            'text': 'aNewText',
            'pub_date': '2024-12-31',
            'pub_time': '23:55:00',
            'category': self.cat.pk,
            'send': True,
        }
        response = self.client.post(f'/{self.article.stamp}/{self.article.slug}/edit/',
                                    data=data,
                                    follow=True)
        self.assertRedirects(response,
                             f'http://ikhaya.{settings.BASE_DOMAIN_NAME}/2024/12/31/anewsubject/')

    def test_edit_article__public__http_get(self):
        self.article.public = True
        self.article.save()

        response = self.client.get(f'/{self.article.stamp}/{self.article.slug}/edit/',
                                   follow=True)
        self.assertNotContains(response, 'slug')

    def test_edit_article__public__http_post(self):
        self.article.public = True
        self.article.save()

        data = {
            'author': self.admin.username,
            'subject': 'aNewSubject',
            'intro': 'aNewIntro',
            'text': 'aNewText',
            'pub_date': '2024-12-31',
            'pub_time': '23:55:00',
            'category': self.cat.pk,
            'send': True,
        }
        response = self.client.post(f'/{self.article.stamp}/{self.article.slug}/edit/',
                                    data=data,
                                    follow=True)
        self.assertRedirects(response,
                             f'http://ikhaya.{settings.BASE_DOMAIN_NAME}/{self.article.stamp}/a1subject/')

        self.article.refresh_from_db()
        self.assertEqual(self.article.slug, 'a1subject')
        self.assertEqual(self.article.subject, 'aNewSubject')

    def test_preview(self):
        response = self.client.post('/article/new/', data={'preview': True, 'intro': 'ArticlePrevIntro', 'text': 'ArticlePrevText'})
        self.assertContains(response, 'ArticlePrevIntro', count=2)
        self.assertContains(response, 'ArticlePrevText', count=2)

    def test_create_new_article(self):
        data = {
            'author': self.admin.username,
            'subject': 'aNewSubject',
            'intro': 'aNewIntro',
            'text': 'aNewText',
            'pub_date': '2024-12-31',
            'pub_time': '23:55:00',
            'category': self.cat.pk,
            'send': True,
        }
        response = self.client.post('/article/new/', data=data, follow=True)

        self.assertEqual(Article.objects.count(), 2)
        self.assertRedirects(response, f'http://ikhaya.{settings.BASE_DOMAIN_NAME}/2024/12/31/anewsubject/edit/')

    def test_create_new_article__http_get(self):
        response = self.client.get('/article/new/', follow=True)

        self.assertContains(response, 'name="slug"', count=1)
        self.assertNotContains(response, 'name="updated"')


class TestArticleSubscribe(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()
        self.admin = User.objects.register_user('admin', 'admin', 'admin', False)
        self.admin.is_superuser = True
        self.admin.save()

        self.user = User.objects.register_user('user', 'user', 'user', False)

        self.cat = Category.objects.create(name="Categrory")
        self.article = Article.objects.create(author=self.admin, subject="a1Subject",
                                              intro="a1Intro", text="a1Text",
                                              pub_date=datetime.datetime.today().date(),
                                              pub_time=datetime.datetime.now().time(),
                                              category=self.cat)

        self.client.defaults['HTTP_HOST'] = 'ikhaya.%s' % settings.BASE_DOMAIN_NAME
        self.client.login(username='admin', password='admin')

    def test_subscribe(self):
        response = self.client.get(f'/{self.article.stamp}/{self.article.slug}/subscribe/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Subscription.objects.count(), 1)
        self.assertRedirects(response, f'http://ikhaya.{settings.BASE_DOMAIN_NAME}/{self.article.stamp}/{self.article.slug}/')

    def test_not_existing_article__status_code(self):
        response = self.client.get('/1785/5/8/goo/subscribe/')
        self.assertEqual(response.status_code, 404)

    def test_not_valid_month__status_code(self):
        response = self.client.get('/1785/a/8/goo/subscribe/')
        self.assertEqual(response.status_code, 404)

    def test_user__http_403(self):
        self.client.login(username='user', password='user')

        response = self.client.get(f'/{self.article.stamp}/{self.article.slug}/subscribe/')
        self.assertEqual(response.status_code, 403)


class TestArticleUnsubscribe(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()
        self.admin = User.objects.register_user('admin', 'admin', 'admin', False)
        self.admin.is_superuser = True
        self.admin.save()

        self.user = User.objects.register_user('user', 'user', 'user', False)

        self.cat = Category.objects.create(name="Categrory")
        self.article = Article.objects.create(author=self.admin, subject="a1Subject",
                                              intro="a1Intro", text="a1Text",
                                              pub_date=datetime.datetime.today().date(),
                                              pub_time=datetime.datetime.now().time(),
                                              category=self.cat)

        self.client.defaults['HTTP_HOST'] = 'ikhaya.%s' % settings.BASE_DOMAIN_NAME
        self.client.login(username='admin', password='admin')

    def test_unsubscribe(self):
        Subscription(user=self.admin, content_object=self.article).save()
        self.assertEqual(Subscription.objects.count(), 1)

        response = self.client.get(f'/{self.article.stamp}/{self.article.slug}/unsubscribe/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Subscription.objects.count(), 0)
        self.assertRedirects(response, f'http://ikhaya.{settings.BASE_DOMAIN_NAME}/{self.article.stamp}/{self.article.slug}/')

    def test_not_existing_article__status_code(self):
        response = self.client.get('/1785/5/8/goo/unsubscribe/')
        self.assertEqual(response.status_code, 404)

    def test_not_valid_month__status_code(self):
        response = self.client.get('/1785/a/8/goo/unsubscribe/')
        self.assertEqual(response.status_code, 404)

    def test_user__no_permission_needed(self):
        self.client.login(username='user', password='user')

        response = self.client.get(f'/{self.article.stamp}/{self.article.slug}/unsubscribe/', follow=True)
        # target status code 403 is OK, as the user can only unsubscribe, but not view the article
        self.assertRedirects(response, f'http://ikhaya.{settings.BASE_DOMAIN_NAME}/{self.article.stamp}/{self.article.slug}/', target_status_code=403)


class TestReportNew(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()
        self.admin = User.objects.register_user('admin', 'admin', 'admin', False)
        self.admin.is_superuser = True
        self.admin.save()

        self.user = User.objects.register_user('user', 'user', 'user', False)

        self.cat = Category.objects.create(name="Categrory")
        self.article = Article.objects.create(author=self.admin, subject="a1Subject",
                                              intro="a1Intro", text="a1Text",
                                              pub_date=datetime.datetime.today().date(),
                                              pub_time=datetime.datetime.now().time(),
                                              category=self.cat)

        self.client.defaults['HTTP_HOST'] = 'ikhaya.%s' % settings.BASE_DOMAIN_NAME
        self.client.login(username='admin', password='admin')

    def test_status_code(self):
        response = self.client.get(f'/{self.article.stamp}/{self.article.slug}/new_report/')
        self.assertEqual(response.status_code, 200)

    def test_not_existing_article_status_code(self):
        response = self.client.get('/1785/5/8/goo/new_report/')
        self.assertEqual(response.status_code, 404)

    def test_preview_rendered(self):
        canary_text = 'canary6718'

        response = self.client.post(f'/{self.article.stamp}/{self.article.slug}/new_report/', {'preview': True, 'text': canary_text})
        self.assertContains(response, canary_text, count=2, html=True)

    def test_post_new_report(self):
        response = self.client.post(f'/{self.article.stamp}/{self.article.slug}/new_report/',
                                    {'send': True, 'text': 'my great new text'}, follow=True)

        self.assertRedirects(response, f'http://ikhaya.{settings.BASE_DOMAIN_NAME}/{self.article.stamp}/a1subject/reports/')
        self.assertEqual(Report.objects.count(), 1)
        self.assertEqual(Report.objects.get().text, 'my great new text')
        self.assertEqual(Report.objects.get().article, self.article)


class TestReports(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()
        self.admin = User.objects.register_user('admin', 'admin', 'admin', False)
        self.admin.is_superuser = True
        self.admin.save()

        self.user = User.objects.register_user('user', 'user', 'user', False)

        self.cat = Category.objects.create(name="Categrory")
        self.article = Article.objects.create(author=self.admin, subject="a1Subject",
                                              intro="a1Intro", text="a1Text",
                                              pub_date=datetime.datetime.today().date(),
                                              pub_time=datetime.datetime.now().time(),
                                              category=self.cat)

        self.client.defaults['HTTP_HOST'] = 'ikhaya.%s' % settings.BASE_DOMAIN_NAME
        self.client.login(username='admin', password='admin')

    def test_status_code(self):
        response = self.client.get(f'/{self.article.stamp}/{self.article.slug}/reports/')
        self.assertEqual(response.status_code, 200)

    def test_not_existing_article_status_code(self):
        response = self.client.get('/1785/5/8/goo/reports/')
        self.assertEqual(response.status_code, 404)

    def test_reports_shown(self):
        unsolved_report = Report.objects.create(
            article=self.article,
            text="unsolvedReport",
            author=self.user,
            pub_date=dj_timezone.now(),
            solved=False,
        )
        solved_report = Report.objects.create(
            article=self.article,
            text="solved_report",
            author=self.admin,
            pub_date=dj_timezone.now(),
            solved=True,
        )

        response = self.client.get(f'/{self.article.stamp}/{self.article.slug}/reports/')
        self.assertContains(response, unsolved_report.text)
        self.assertContains(response, solved_report.text)


class TestReportList(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()
        self.admin = User.objects.register_user('admin', 'admin', 'admin', False)
        self.admin.is_superuser = True
        self.admin.save()

        self.user = User.objects.register_user('user', 'user', 'user', False)

        self.cat = Category.objects.create(name="Categrory")
        self.article = Article.objects.create(author=self.admin, subject="a1Subject",
                                              intro="a1Intro", text="a1Text",
                                              pub_date=datetime.datetime.today().date(),
                                              pub_time=datetime.datetime.now().time(),
                                              category=self.cat)

        self.client.defaults['HTTP_HOST'] = 'ikhaya.%s' % settings.BASE_DOMAIN_NAME
        self.client.login(username='admin', password='admin')

    def test_unsolved_report_shown(self):
        unsolved_report = Report.objects.create(
            article=self.article,
            text="unsolvedReport",
            author=self.user,
            pub_date=dj_timezone.now(),
            solved=False,
        )

        response = self.client.get('/reports/')
        self.assertContains(response, unsolved_report.text)

    def test_solved_report_not_shown(self):
        solved_report = Report.objects.create(
            article=self.article,
            text="solved_report",
            author=self.admin,
            pub_date=dj_timezone.now(),
            solved=True,
        )

        response = self.client.get('/reports/')
        self.assertNotContains(response, solved_report.text)

    def test_deleted_report_not_shown(self):
        deleted_report = Report.objects.create(
            article=self.article,
            text="del_report",
            author=self.admin,
            pub_date=dj_timezone.now(),
            deleted=True,
        )

        response = self.client.get('/reports/')
        self.assertNotContains(response, deleted_report.text)

    def test_user__permission_missing(self):
        self.client.login(username='user', password='user')

        response = self.client.get('/reports/')
        self.assertEqual(response.status_code, 403)


class TestCommentEdit(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()
        self.admin = User.objects.register_user('admin', 'admin', 'admin', False)
        self.admin.is_superuser = True
        self.admin.save()

        self.user = User.objects.register_user('user', 'user', 'user', False)

        self.cat = Category.objects.create(name="Categrory")
        self.article = Article.objects.create(author=self.admin, subject="a1Subject",
                                              intro="a1Intro", text="a1Text",
                                              pub_date=datetime.datetime.today().date(),
                                              pub_time=datetime.datetime.now().time(),
                                              category=self.cat)

        self.client.defaults['HTTP_HOST'] = 'ikhaya.%s' % settings.BASE_DOMAIN_NAME
        self.client.login(username='admin', password='admin')

        self.comment = Comment.objects.create(article=self.article, text="Text",
                                              author=self.user,
                                              pub_date=dj_timezone.now(),)

    def test_not_existing_comment(self):
        response = self.client.get('/comment/1337/edit/')
        self.assertEqual(response.status_code, 404)

    def test_user__is_comment_author__permission_missing(self):
        self.client.login(username='user', password='user')

        response = self.client.get(f'/comment/{self.comment.id}/edit/', follow=True)
        self.assertRedirects(response, f'http://ikhaya.{settings.BASE_DOMAIN_NAME}/{self.article.stamp}/a1subject/', target_status_code=403)

    def test_user__permission_missing(self):
        self.comment.author = self.admin
        self.comment.save()

        self.client.login(username='user', password='user')

        response = self.client.get(f'/comment/{self.comment.id}/edit/')
        self.assertEqual(response.status_code, 403)

    def test_status_code(self):
        response = self.client.get(f'/comment/{self.comment.id}/edit/')
        self.assertEqual(response.status_code, 200)

    def test_edit_comment(self):
        response = self.client.post(f'/comment/{self.comment.id}/edit/', data={'text': 'newCommentText'}, follow=True)
        self.assertRedirects(response, f'http://ikhaya.{settings.BASE_DOMAIN_NAME}/{self.article.stamp}/a1subject/#comment_1')

        self.comment.refresh_from_db()
        self.assertEqual(self.comment.text, 'newCommentText')


class TestArchive(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()

        self.admin = User.objects.register_user('admin', 'admin', 'admin', False)
        self.admin.is_superuser = True
        self.admin.save()

        self.user = User.objects.register_user('user', 'user', 'user', False)

        self.cat = Category.objects.create(name="Category")

        self.client.defaults['HTTP_HOST'] = 'ikhaya.%s' % settings.BASE_DOMAIN_NAME
        self.client.login(username='admin', password='admin')

    def test_no_article(self):
        response = self.client.get('/archive/')
        self.assertEqual(response.status_code, 200)

    def test_months(self):
        for i in range(1, 12):
            Article.objects.create(author=self.admin, subject=f"a{i}Subject",
                                   intro=f"a{i}Intro", text=f"a{i}Text",
                                   pub_date=datetime.date(2005, i, 2),
                                   pub_time=datetime.time(12, 0),
                                   category=self.cat,
                                   public=True,
                                   )

        Article.objects.create(author=self.user, subject="aLastSubject",
                               intro="aLastIntro", text="aLastText",
                               pub_date=datetime.date(2004, 5, 12),
                               pub_time=datetime.time(13, 0),
                               category=self.cat,
                               public=True,
                               )

        response = self.client.get('/archive/')
        self.assertEqual(list(response.context['months']),
                         [datetime.date(2004, 5, 1),
                          datetime.date(2005, 1, 1),
                          datetime.date(2005, 2, 1),
                          datetime.date(2005, 3, 1),
                          datetime.date(2005, 4, 1),
                          datetime.date(2005, 5, 1),
                          datetime.date(2005, 6, 1),
                          datetime.date(2005, 7, 1),
                          datetime.date(2005, 8, 1),
                          datetime.date(2005, 9, 1),
                          datetime.date(2005, 10, 1),
                          datetime.date(2005, 11, 1),
                          ]
                         )


class TestSuggestionAssign(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()

        self.admin = User.objects.register_user('admin', 'admin', 'admin', False)
        self.admin.is_superuser = True
        self.admin.save()

        self.user = User.objects.register_user('user', 'user', 'user', False)

        self.cat = Category.objects.create(name="Category")

        self.client.defaults['HTTP_HOST'] = 'ikhaya.%s' % settings.BASE_DOMAIN_NAME
        self.client.login(username='admin', password='admin')

        self.suggestion = Suggestion.objects.create(author=self.admin,
                                                    title='SugTitle',
                                                    intro='SugIntro',
                                                    text='SugText',
                                                    notes='SugNotes',
                                                    )

    def test_not_existing_suggestion(self):
        response = self.client.get(f'/suggest/1337/assign/{self.admin}/', follow=True)
        self.assertRedirects(response, href('ikhaya', 'suggestions'))
        self.assertContains(response, 'does not exist', count=1)

    def test_no_permission(self):
        self.client.login(username='user', password='user')

        response = self.client.get(f'/suggest/{self.suggestion.id}/assign/{self.admin}/')
        self.assertEqual(response.status_code, 403)

    def test_delete_assignee(self):
        self.suggestion.owner = self.admin
        self.suggestion.save()

        self.client.get(f'/suggest/{self.suggestion.id}/assign/-/')

        self.suggestion.refresh_from_db()
        self.assertEqual(self.suggestion.owner, None)

    def test_assign_yourself(self):
        self.client.get(
            f'/suggest/{self.suggestion.id}/assign/{self.admin}/')

        self.suggestion.refresh_from_db()
        self.assertEqual(self.suggestion.owner, self.admin)

    def test_assign_other_user_fails(self):
        self.client.get(
            f'/suggest/{self.suggestion.id}/assign/{self.user}/')

        self.suggestion.refresh_from_db()
        self.assertEqual(self.suggestion.owner, None)


class TestSuggestDelete(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()

        self.admin = User.objects.register_user('admin', 'admin@inyoka.test', 'admin', False)
        self.admin.is_superuser = True
        self.admin.save()

        self.user = User.objects.register_user('user', 'user', 'user', False)

        self.cat = Category.objects.create(name="Category")

        self.client.defaults['HTTP_HOST'] = 'ikhaya.%s' % settings.BASE_DOMAIN_NAME
        self.client.login(username='admin', password='admin')

        self.suggestion = Suggestion.objects.create(author=self.admin,
                                                    title='SugTitle',
                                                    intro='SugIntro',
                                                    text='SugText',
                                                    notes='SugNotes',
                                                    )

    def test_status_code(self):
        response = self.client.get(f'/suggest/{self.suggestion.id}/delete/', follow=True)
        self.assertRedirects(response, href('ikhaya', 'suggestions'))

    def test_not_existing_suggestion__http_get(self):
        response = self.client.get('/suggest/1337/delete/', follow=True)
        self.assertRedirects(response, href('ikhaya', 'suggestions'))
        self.assertContains(response, 'does not exist', count=1)

    def test_not_existing_suggestion__http_post(self):
        response = self.client.post('/suggest/1337/delete/', data={}, follow=True)
        self.assertRedirects(response, href('ikhaya', 'suggestions'))
        self.assertContains(response, 'does not exist', count=1)

    def test_no_permission(self):
        self.client.login(username='user', password='user')

        response = self.client.get(f'/suggest/{self.suggestion.id}/delete/')
        self.assertEqual(response.status_code, 403)

    def test_cancel(self):
        response = self.client.post(f'/suggest/{self.suggestion.id}/delete/',
                                   data={'cancel': True},
                                   follow=True)
        self.assertRedirects(response, href('ikhaya', 'suggestions'))
        self.assertEqual(Suggestion.objects.count(), 1)

    def test_delete(self):
        response = self.client.post(f'/suggest/{self.suggestion.id}/delete/',
                                   data={},
                                   follow=True)
        self.assertRedirects(response, href('ikhaya', 'suggestions'))
        self.assertEqual(Suggestion.objects.count(), 0)

    def test_delete__private_message_send(self):
        response = self.client.post(f'/suggest/{self.suggestion.id}/delete/',
                                   data={'note': 'SuggestionNoteRejected'},
                                   follow=True)
        self.assertRedirects(response, href('ikhaya', 'suggestions'))
        self.assertEqual(Suggestion.objects.count(), 0)

        self.assertEqual(PrivateMessage.objects.count(), 1)
        self.assertEqual(PrivateMessageEntry.objects.count(), 2)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'inyokaproject.org: New private message from admin: Article suggestion rejected')


class TestSuggestEdit(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()

        self.admin = User.objects.register_user('admin', 'admin@inyoka.test', 'admin', False)
        self.admin.is_superuser = True
        self.admin.save()

        self.user = User.objects.register_user('user', 'user', 'user', False)

        self.cat = Category.objects.create(name="Category")

        self.client.defaults['HTTP_HOST'] = 'ikhaya.%s' % settings.BASE_DOMAIN_NAME
        self.client.login(username='admin', password='admin')

    def test_status_code(self):
        response = self.client.get('/suggest/new/')
        self.assertEqual(response.status_code, 200)

    def test_no_permission(self):
        self.client.login(username='user', password='user')

        response = self.client.get('/suggest/new/')
        self.assertEqual(response.status_code, 403)

    def test_preview(self):
        response = self.client.post('/suggest/new/',
                                    data={'text': 'SugPreviewText', 'preview': True})
        self.assertContains(response, 'SugPreviewText', count=2)

    def test_submit_suggestion(self):
        response = self.client.post('/suggest/new/',
                                    data={'title': 'SugTitle',
                                            'intro': 'SugIntro',
                                            'text': 'SugText',
                                            'notes': 'SugNotes',
                                          }, follow=True)
        self.assertRedirects(response, href('ikhaya'))

        self.assertEqual(Suggestion.objects.count(), 1)
        suggestion = Suggestion.objects.get()
        self.assertEqual(suggestion.author, self.admin)

    @patch('inyoka.ikhaya.views.send_new_suggestion_notifications')
    def test_submit_suggestion__notification_submitted(self, mock):
        self.client.post('/suggest/new/',
                                    data={'title': 'SugTitle',
                                            'intro': 'SugIntro',
                                            'text': 'SugText',
                                            'notes': 'SugNotes',
                                          }, follow=True)

        suggestion = Suggestion.objects.get()
        mock.assert_called_once_with(self.admin.pk, suggestion.pk)


class TestSuggestions(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()

        self.admin = User.objects.register_user('admin', 'admin@inyoka.test', 'admin', False)
        self.admin.is_superuser = True
        self.admin.save()

        self.user = User.objects.register_user('user', 'user', 'user', False)

        self.cat = Category.objects.create(name="Category")

        self.client.defaults['HTTP_HOST'] = 'ikhaya.%s' % settings.BASE_DOMAIN_NAME
        self.client.login(username='admin', password='admin')

        self.suggestion = Suggestion.objects.create(author=self.admin,
                                                    title='SugTitle',
                                                    intro='SugIntro',
                                                    text='SugText',
                                                    notes='SugNotes',
                                                    )

    def test_content(self):
        response = self.client.get('/suggestions/')
        self.assertContains(response, 'SugTitle')

    def test_no_permission(self):
        self.client.login(username='user', password='user')

        response = self.client.get('/suggestions/')
        self.assertEqual(response.status_code, 403)


class TestSubscribe(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()

        self.admin = User.objects.register_user('admin', 'admin@inyoka.test', 'admin', False)
        self.admin.is_superuser = True
        self.admin.save()

        self.user = User.objects.register_user('user', 'user', 'user', False)

        self.cat = Category.objects.create(name="Category")

        self.client.defaults['HTTP_HOST'] = 'ikhaya.%s' % settings.BASE_DOMAIN_NAME
        self.client.login(username='admin', password='admin')

    def test_subscription_created(self):
        response = self.client.get('/suggestions/subscribe/', follow=True)
        self.assertContains(response, 'Notifications on new suggestions')

        # if no exception is raised, it exists
        Subscription.objects.get_for_user(self.admin, None, ['ikhaya', 'suggestion'])

    def test_subscription_already_exists(self):
        ct = ContentType.objects.get_by_natural_key(*['ikhaya', 'suggestion'])
        Subscription(user=self.admin, content_type=ct).save()

        response = self.client.get('/suggestions/subscribe/', follow=True)
        self.assertRedirects(response, href('ikhaya', 'suggestions'))

    def test_no_permission(self):
        self.client.login(username='user', password='user')

        response = self.client.get('/suggestions/subscribe/')
        self.assertEqual(response.status_code, 403)


class TestUnsubscribe(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()

        self.admin = User.objects.register_user('admin', 'admin@inyoka.test', 'admin', False)
        self.admin.is_superuser = True
        self.admin.save()

        self.user = User.objects.register_user('user', 'user', 'user', False)

        self.cat = Category.objects.create(name="Category")

        self.client.defaults['HTTP_HOST'] = 'ikhaya.%s' % settings.BASE_DOMAIN_NAME
        self.client.login(username='admin', password='admin')

    def test_subscription_removed(self):
        ct = ContentType.objects.get_by_natural_key(*['ikhaya', 'suggestion'])
        Subscription(user=self.admin, content_type=ct).save()

        response = self.client.get('/suggestions/unsubscribe/', follow=True)
        self.assertContains(response, 'No notifications on suggestions')

        with self.assertRaises(Subscription.DoesNotExist):
            Subscription.objects.get_for_user(self.admin, None, ['ikhaya', 'suggestion'])

    def test_subscription_not_existing(self):
        with self.assertRaises(Subscription.DoesNotExist):
            Subscription.objects.get_for_user(self.admin, None, ['ikhaya', 'suggestion'])

        response = self.client.get('/suggestions/unsubscribe/', follow=True)
        self.assertRedirects(response, href('ikhaya', 'suggestions'))

        with self.assertRaises(Subscription.DoesNotExist):
            Subscription.objects.get_for_user(self.admin, None, ['ikhaya', 'suggestion'])

    def test_no_permission(self):
        self.client.login(username='user', password='user')

        response = self.client.get('/suggestions/unsubscribe/')
        self.assertEqual(response.status_code, 403)


class TestEventView(TestCase):

    client_class = InyokaClient

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.register_user('test', 'test@example.local', password='test', send_mail=False)
        group = Group.objects.create(name='test_event_group')
        assign_perm('portal.change_event', group)
        group.user_set.add(self.user)

        self.client.defaults['HTTP_HOST'] = 'ikhaya.%s' % settings.BASE_DOMAIN_NAME
        self.client.login(username='test', password='test')

    def test_user_can_view_it(self):
        response = self.client.get('/events/')
        self.assertEqual(response.status_code, 200)

    def test_anonymous_gets_error(self):
        request = self.factory.get('/')
        request.user = User.objects.get_anonymous_user()
        with self.assertRaises(PermissionDenied):
            events(request)

    def test_queries_needed(self):
        with self.assertNumQueries(10):
            self.client.get('/events/')


class TestEventDelete(TestCase):

    client_class = InyokaClient

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.register_user('test', 'test@example.test', password='test', send_mail=False)
        group = Group.objects.create(name='test_event_group')
        assign_perm('portal.delete_event', group)
        assign_perm('portal.change_event', group)
        group.user_set.add(self.user)

        self.client.defaults['HTTP_HOST'] = 'ikhaya.%s' % settings.BASE_DOMAIN_NAME
        self.client.login(username='test', password='test')

        self.event = Event.objects.create(
            name='Event',
            date=datetime.datetime.now(datetime.UTC).date() + datetime.timedelta(days=0),
            enddate=datetime.datetime.now(datetime.UTC).date() + datetime.timedelta(days=1),
            author=self.user,
            visible=False
        )

    def test_status_code(self):
        url = f'/event/{self.event.id}/delete/'
        response = self.client.get(url, follow=True)

        host = self.client.defaults['HTTP_HOST']
        self.assertRedirects(response, f'http://{host}/events/')

    def test_anonymous_no_permission(self):
        request = self.factory.get(f'/event/{self.event.id}/delete/')
        request.user = User.objects.get_anonymous_user()

        response = event_delete(request)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith(f"/login/?next=http%3A//testserver/event/{self.event.id}/delete/"))

    def test_displays_form(self):
        response = self.client.get(f'/event/{self.event.id}/delete/', follow=True)
        self.assertContains(response, 'Do you really want to delete the event')

    def test_event_delete(self):
        self.assertEqual(Event.objects.count(), 1)

        response = self.client.post(f'/event/{self.event.id}/delete/', data={'submit': 'Delete'})
        self.assertEqual(Event.objects.count(), 0)
        self.assertEqual(response.status_code, 302)

        host = self.client.defaults['HTTP_HOST']
        self.assertEqual(response.url, f'http://{host}/events/')

    def test_event_delete__message(self):
        response = self.client.post(f'/event/{self.event.id}/delete/', data={'submit': 'Delete'}, follow=True)
        self.assertContains(response, 'event “Event” was deleted successfully!')

    def test_event_delete__cancel(self):
        response = self.client.post(f'/event/{self.event.id}/delete/', data={'cancel': 'cancel'}, follow=True)
        self.assertContains(response, 'Canceled.')


class TestEventEdit(TestCase):

    client_class = InyokaClient

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.register_user('test', 'test@example.test', password='test', send_mail=False)

        group = Group.objects.create(name='test_event_group')
        assign_perm('portal.change_event', group)
        assign_perm('portal.add_event', group)
        group.user_set.add(self.user)

        self.client.defaults['HTTP_HOST'] = 'ikhaya.%s' % settings.BASE_DOMAIN_NAME
        self.client.login(username='test', password='test')

        self.event = Event.objects.create(
            name='Event',
            date=dj_timezone.now(),
            author=self.user,
            visible=False
        )

    def test_status_code__new_event__http_get(self):
        response = self.client.get('/event/new/')
        self.assertEqual(response.status_code, 200)

    def test_status_code__edit_event__http_get(self):
        response = self.client.get(f'/event/{self.event.id}/edit/')
        self.assertEqual(response.status_code, 200)

    def test_anonymous_no_permission(self):
        request = self.factory.get('')
        request.user = User.objects.get_anonymous_user()

        with self.assertRaises(PermissionDenied):
            event_edit(request)

    def test_user_no_add_permission(self):
        group =Group.objects.get(name='test_event_group')
        remove_perm('portal.add_event', group)

        request = self.factory.get('')
        request.user = self.user

        with self.assertRaises(PermissionDenied):
            event_edit(request)

    def test_modify_event__http_post(self):
        data = {
            'name': 'EventEdited',
            'date': '2016-01-16',
        }
        self.client.post(f'/event/{self.event.id}/edit/', data=data, follow=True)

        self.event.refresh_from_db()
        self.assertEqual(self.event.name, data['name'])

    def test_new_event__http_post(self):
        data = {
            'name': 'New Event',
            'date': '2016-01-16',
        }
        response = self.client.post('/event/new/', data=data)
        self.assertEqual(Event.objects.count(), 2)

        e = Event.objects.exclude(pk=self.event.pk).get()
        self.assertEqual(e.name, data['name'])

        # dont fetch response, as on different subdomain
        self.assertRedirects(response, f'http://{settings.BASE_DOMAIN_NAME}/calendar/2016/01/16/new-event/', fetch_redirect_response=False)

    def test_copy_event__http_get(self):
        self.event.visible = True
        self.event.location_town = 'Bärlin (sic)'
        self.event.save()

        response = self.client.get(f'/event/new/?copy_from={self.event.id}')
        self.assertContains(response, 'name="name" value="Event"')
        self.assertContains(response, 'Bärlin')

    def test_copy_event_to_existing_event__http_get(self):
        """
        The copy_from parameter can not only be used for new events, it can also
        populate the form fields of an existing event
        """
        self.event.location_town = 'Bärlin (sic)'
        self.event.save()

        event2 = Event.objects.create(
            name='SecondEvent',
            date=dj_timezone.now(),
            author=self.user,
            visible=True
        )

        response = self.client.get(f'/event/{event2.id}/edit/?copy_from={self.event.id}')
        self.assertContains(response, 'name="name" value="Event"')
        self.assertContains(response, 'Bärlin')

    def test_copy_event__not_existing(self):
        response = self.client.get('/event/new/?copy_from=1337')
        self.assertContains(response, 'because it does not exist')

    def test_copy_event__text_parameter(self):
        response = self.client.get('/event/new/?copy_from=<script>console.log("foo")</script>')
        self.assertContains(response, 'is not a number')


class TestServices(TestCase):

    client_class = InyokaClient
    url = "/?__service__=ikhaya.change_suggestion_assignment"

    def test_post_misses_username(self):
        response = self.client.post(self.url, data={"suggestion": 1})
        self.assertEqual(response.status_code, 400)

    def test_post_misses_suggestion_id(self):
        response = self.client.post(self.url, data={"username": "foo"})
        self.assertEqual(response.status_code, 400)

    def test_set_owner(self):
        user = User.objects.register_user('test', 'test@example.local', password='test', send_mail=False)
        suggestion = Suggestion.objects.create(author=user, title='title', text='text', intro='intro', notes='notes')
        self.assertIsNone(suggestion.owner)

        self.client.post(self.url, data={"username": user.username, "suggestion": suggestion.id})
        suggestion.refresh_from_db()
        self.assertEqual(suggestion.owner_id, user.id)

        self.client.post(self.url, data={"username": "-", "suggestion": suggestion.id})
        suggestion.refresh_from_db()
        self.assertIsNone(suggestion.owner)

    def test_invalid_owner(self):
        suggestion = Suggestion.objects.create(
            author=User.objects.get_anonymous_user(), title='title', text='text', intro='intro', notes='notes')

        response = self.client.post(self.url, data={"username": "foo", "suggestion": suggestion.id})
        self.assertEqual(response.status_code, 404)

    def test_invalid_suggestion(self):
        user = User.objects.register_user('test', 'test@example.local', password='test', send_mail=False)

        response = self.client.post(self.url, data={"username": user.username, "suggestion": 4242})
        self.assertEqual(response.status_code, 404)


@freeze_time("2023-12-09T23:55:04Z")
class TestArticleFeeds(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()

        self.now = dj_timezone.now().replace(microsecond=0)
        now = self.now
        today = now.date()
        time_now = now.time()

        self.admin = User.objects.register_user('admin', 'admin', 'admin', False)
        self.user = User.objects.register_user('user', 'user', 'user', False)
        self.admin.is_superuser = True
        self.admin.save()

        self.cat = Category.objects.create(name="Category")
        self.article = Article.objects.create(author=self.admin, subject="Subject",
                            text="Text", pub_date=today,
                            pub_time=time_now, category=self.cat, public=True)
        self.comment = Comment.objects.create(article=self.article, text="Text",
                            author=self.user, pub_date=now)

        self.client.defaults['HTTP_HOST'] = 'ikhaya.%s' % settings.BASE_DOMAIN_NAME

    def test_modes(self):
        response = self.client.get('/feeds/short/10/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/feeds/title/20/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/feeds/full/50/')
        self.assertEqual(response.status_code, 200)

    def test_queries(self):
        with self.assertNumQueries(4):
            self.client.get('/feeds/full/50/')

    def test_multiple_articles(self):
        today = self.now.date()
        time_now = self.now.time()

        self.article = Article.objects.create(author=self.admin, subject="Subject 2",
                            text="Text 2", pub_date=today,
                            pub_time=time_now, category=self.cat, public=True)

        response = self.client.get('/feeds/full/10/')
        self.assertIn(self.article.subject, response.content.decode())

        feed = feedparser.parse(response.content)
        self.assertEqual(len(feed.entries), 2)

    def test_content_exact(self):
        storage['ikhaya_description_rendered'] = 'Just to describe ikhaya'

        response = self.client.get('/feeds/full/10/')

        self.maxDiff = None
        self.assertXMLEqual(response.content.decode(),
'''<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="en-us">
  <title>ubuntuusers.local:8080 Ikhaya</title>
  <link href="http://ikhaya.ubuntuusers.local:8080/" rel="alternate"/>
  <link href="http://ikhaya.ubuntuusers.local:8080/feeds/full/10/" rel="self" />
  <id>http://ikhaya.ubuntuusers.local:8080/</id>
  <updated>2023-12-10T00:55:04+01:00</updated>
  <subtitle>Just to describe ikhaya</subtitle>
  <rights>http://ubuntuusers.local:8080/lizenz/</rights>
  <entry>
    <title>Subject</title>
    <link href="http://ikhaya.ubuntuusers.local:8080/2023/12/09/subject/" rel="alternate"/>
    <published>2023-12-10T00:55:04+01:00</published>
    <updated>2023-12-10T00:55:04+01:00</updated>
    <author>
      <name>admin</name>
      <uri>http://ubuntuusers.local:8080/user/admin/</uri>
    </author>
    <id>http://ikhaya.ubuntuusers.local:8080/2023/12/09/subject/</id>
    <summary type="html">
&lt;p&gt;Text&lt;/p&gt;</summary>
    <category term="Category"/>
  </entry>
</feed>
''')

    def test_content_displayed(self):
        storage['ikhaya_description_rendered'] = 'Just to describe ikhaya'

        response = self.client.get('/feeds/full/10/')

        feed = feedparser.parse(response.content)

        # feed properties
        self.assertEqual(feed.feed.title, 'ubuntuusers.local:8080 Ikhaya')
        self.assertEqual(feed.feed.subtitle, 'Just to describe ikhaya')
        self.assertEqual(feed.feed.title_detail.type, 'text/plain')
        self.assertEqual(feed.feed.title_detail.language, 'en-us')
        self.assertEqual(feed.feed.id, 'http://ikhaya.ubuntuusers.local:8080/')
        self.assertEqual(feed.feed.link, 'http://ikhaya.ubuntuusers.local:8080/')

        now_utc = self.now
        now_utc = now_utc.replace(tzinfo=zoneinfo.ZoneInfo("Europe/London"))

        feed_updated = parse_datetime(feed.feed.updated)
        self.assertEqual(feed_updated, now_utc)

        self.assertEqual(feed.feed.rights, href('portal', 'lizenz'))
        self.assertNotIn('author', feed.feed)
        self.assertNotIn('author_detail', feed.feed)

        # entry properties
        self.assertEqual(len(feed.entries), 1)
        entry = feed.entries[0]

        url = f'http://ikhaya.ubuntuusers.local:8080/{self.now.year}/{self.now.month:02d}/{self.now.day:02d}/subject/'
        self.assertEqual(entry.id, url)
        self.assertEqual(entry.link, url)

        self.assertEqual(entry.title_detail.value, 'Subject')
        self.assertEqual(entry.title_detail.type, 'text/plain')
        self.assertEqual(entry.summary, '<p>Text</p>')
        self.assertEqual(entry.summary_detail.type, 'text/html')
        self.assertNotIn('text', entry)
        self.assertNotIn('created_parsed', entry)

        entry_published = parse_datetime(entry.published)
        self.assertEqual(entry_published, now_utc)

        entry_date = parse_datetime(entry.date)
        self.assertEqual(entry_date, now_utc)

        entry_updated = parse_datetime(entry.updated)
        self.assertEqual(entry_updated, now_utc)

        self.assertEqual(entry.author, self.admin.username)
        self.assertEqual(entry.author_detail.name, self.admin.username)
        self.assertEqual(entry.author_detail.href, 'http://ubuntuusers.local:8080/user/admin/')


@freeze_time("2023-12-09T23:55:04Z")
class TestArticleCategoryFeeds(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()

        self.now = datetime.datetime.now().replace(microsecond=0)
        self.today = self.now.date()
        self.time_now = self.now.time()

        self.admin = User.objects.register_user('admin', 'admin', 'admin', False)
        self.user = User.objects.register_user('user', 'user', 'user', False)
        self.admin.is_superuser = True
        self.admin.save()

        self.cat = Category.objects.create(name="Test Category")
        self.article = Article.objects.create(author=self.admin, subject="Subject",
                            text="Text", pub_date=self.today,
                            pub_time=self.time_now, category=self.cat, public=True)

        self.client.defaults['HTTP_HOST'] = 'ikhaya.%s' % settings.BASE_DOMAIN_NAME

        storage['ikhaya_description_rendered'] = 'Just to describe ikhaya'

    def test_modes(self):
        response = self.client.get(f'/feeds/{self.cat.slug}/short/10/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(f'/feeds/{self.cat.slug}/title/20/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(f'/feeds/{self.cat.slug}/full/50/')
        self.assertEqual(response.status_code, 200)

    def test_queries(self):
        with self.assertNumQueries(3):
            self.client.get(f'/feeds/{self.cat.slug}/full/50/')

    def test_multiple_articles(self):
        self.article = Article.objects.create(author=self.admin, subject="Subject 2",
                            text="Text 2", pub_date=self.today,
                            pub_time=self.time_now, category=self.cat, public=True)

        response = self.client.get(f'/feeds/{self.cat.slug}/full/10/')
        self.assertIn(self.article.subject, response.content.decode())

        feed = feedparser.parse(response.content)
        self.assertEqual(len(feed.entries), 2)

    def test_content_exact(self):
        response = self.client.get(f'/feeds/{self.cat.slug}/full/10/')

        Article.objects.create(author=self.admin, subject="Another article in another category",
                               text="Text 2", pub_date=self.today,
                               pub_time=self.time_now, category=Category.objects.create(name="Another"), public=True)

        self.maxDiff = None
        self.assertXMLEqual(response.content.decode(),
'''<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="en-us">
  <title>ubuntuusers.local:8080 Ikhaya – test-category</title>
  <link href="http://ikhaya.ubuntuusers.local:8080/category/test-category/" rel="alternate" />
  <link href="http://ikhaya.ubuntuusers.local:8080/feeds/test-category/full/10/" rel="self" />
  <id>http://ikhaya.ubuntuusers.local:8080/category/test-category/</id>
  <updated>2023-12-10T00:55:04+01:00</updated>
  <subtitle>Just to describe ikhaya</subtitle>
  <rights>http://ubuntuusers.local:8080/lizenz/</rights>
  <entry>
    <title>Subject</title>
    <link href="http://ikhaya.ubuntuusers.local:8080/2023/12/09/subject/" rel="alternate"/>
    <published>2023-12-10T00:55:04+01:00</published>
    <updated>2023-12-10T00:55:04+01:00</updated>
    <author>
      <name>admin</name>
      <uri>http://ubuntuusers.local:8080/user/admin/</uri>
    </author>
    <id>http://ikhaya.ubuntuusers.local:8080/2023/12/09/subject/</id>
    <summary type="html">
&lt;p&gt;Text&lt;/p&gt;</summary>
    <category term="Test Category"/>
  </entry>
</feed>
''')


@freeze_time("2023-12-09T23:55:04Z")
class TestCommentsFeed(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()

        self.now = dj_timezone.now().replace(microsecond=0)
        self.today = self.now.date()
        self.time_now = self.now.time()

        self.admin = User.objects.register_user('admin', 'admin', 'admin', False)
        self.user = User.objects.register_user('user', 'user', 'user', False)
        self.admin.is_superuser = True
        self.admin.save()

        self.cat = Category.objects.create(name="Test Category")
        self.article = Article.objects.create(author=self.admin, subject="Article Subject",
                            text="Text", pub_date=self.today,
                            pub_time=self.time_now, category=self.cat, public=True)

        self.comment = Comment.objects.create(article=self.article, text="Text",
                            author=self.user, pub_date=self.now)

        self.client.defaults['HTTP_HOST'] = 'ikhaya.%s' % settings.BASE_DOMAIN_NAME

        storage['ikhaya_description_rendered'] = '<em>Just</em> to describe ikhaya'

    def test_modes(self):
        response = self.client.get('/feeds/comments/short/10/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/feeds/comments/title/20/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/feeds/comments/full/50/')
        self.assertEqual(response.status_code, 200)

    def test_queries(self):
        with self.assertNumQueries(3):
            self.client.get('/feeds/comments/full/50/')

    def test_multiple_comments(self):
        self.comment = Comment.objects.create(article=self.article, text="Some other Text",
                            author=self.user, pub_date=self.now)

        response = self.client.get('/feeds/comments/full/10/')
        self.assertIn(self.article.subject, response.content.decode())

        feed = feedparser.parse(response.content)
        self.assertEqual(len(feed.entries), 2)

    def test_content_exact(self):
        response = self.client.get('/feeds/comments/full/10/')

        self.maxDiff = None
        self.assertXMLEqual(response.content.decode(),
'''<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="en-us">
  <title>ubuntuusers.local:8080 Ikhaya comments</title>
  <link href="http://ikhaya.ubuntuusers.local:8080/" rel="alternate" />
  <link href="http://ikhaya.ubuntuusers.local:8080/feeds/comments/full/10/" rel="self" />
  <id>http://ikhaya.ubuntuusers.local:8080/</id>
  <updated>2023-12-10T00:55:04+01:00</updated>
  <subtitle>Just to describe ikhaya</subtitle>
  <rights>http://ubuntuusers.local:8080/lizenz/</rights>
  <entry>
    <title>Re: Article Subject</title>
    <link href="http://ikhaya.ubuntuusers.local:8080/2023/12/09/article-subject/#comment_1" rel="alternate"/>
    <published>2023-12-10T00:55:04+01:00</published>
    <updated>2023-12-10T00:55:04+01:00</updated>
    <author>
      <name>user</name>
      <uri>http://ubuntuusers.local:8080/user/user/</uri>
    </author>
    <id>http://ikhaya.ubuntuusers.local:8080/2023/12/09/article-subject/#comment_1</id>
    <summary type="html">&lt;p&gt;Text&lt;/p&gt;</summary>
  </entry>
</feed>
''')


@freeze_time("2023-12-09T23:55:04Z")
class TestCommentsPerArticleFeed(TestCase):

    client_class = InyokaClient

    def setUp(self):
        super().setUp()

        self.now = dj_timezone.now().replace(microsecond=0)
        self.today = self.now.date()
        self.time_now = self.now.time()

        self.admin = User.objects.register_user('admin', 'admin', 'admin', False)
        self.user = User.objects.register_user('user', 'user', 'user', False)
        self.admin.is_superuser = True
        self.admin.save()

        self.cat = Category.objects.create(name="Test Category")
        self.article = Article.objects.create(author=self.admin, subject="Article Subject",
                            text="Text", pub_date=self.today,
                            pub_time=self.time_now, category=self.cat, public=True, id=1)

        self.comment = Comment.objects.create(article=self.article, text="Text",
                            author=self.user, pub_date=self.now)

        self.client.defaults['HTTP_HOST'] = 'ikhaya.%s' % settings.BASE_DOMAIN_NAME

        storage['ikhaya_description_rendered'] = 'Just to describe ikhaya'

    def test_modes(self):
        response = self.client.get(f'/feeds/comments/{self.article.id}/short/10/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(f'/feeds/comments/{self.article.id}/title/20/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(f'/feeds/comments/{self.article.id}/full/50/')
        self.assertEqual(response.status_code, 200)

    def test_queries(self):
        with self.assertNumQueries(4):
            self.client.get(f'/feeds/comments/{self.article.id}/full/50/')

    def test_multiple_comments(self):
        self.comment = Comment.objects.create(article=self.article, text="Some other Text",
                            author=self.user, pub_date=self.now)

        response = self.client.get(f'/feeds/comments/{self.article.id}/full/10/')
        self.assertIn(self.article.subject, response.content.decode())

        feed = feedparser.parse(response.content)
        self.assertEqual(len(feed.entries), 2)

    def test_content_exact(self):
        response = self.client.get(f'/feeds/comments/{self.article.id}/full/10/')

        self.maxDiff = None
        self.assertXMLEqual(response.content.decode(),
'''<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="en-us">
  <title>ubuntuusers.local:8080 Ikhaya comments – Article Subject</title>
  <link href="http://ikhaya.ubuntuusers.local:8080/2023/12/09/article-subject/" rel="alternate"/>
  <link href="http://ikhaya.ubuntuusers.local:8080/feeds/comments/1/full/10/" rel="self" />
  <id>http://ikhaya.ubuntuusers.local:8080/2023/12/09/article-subject/</id>
  <updated>2023-12-10T00:55:04+01:00</updated>
  <subtitle>Just to describe ikhaya</subtitle>
  <rights>http://ubuntuusers.local:8080/lizenz/</rights>
  <entry>
    <title>Re: Article Subject</title>
    <link href="http://ikhaya.ubuntuusers.local:8080/2023/12/09/article-subject/#comment_1" rel="alternate"/>
    <published>2023-12-10T00:55:04+01:00</published>
    <updated>2023-12-10T00:55:04+01:00</updated>
    <author>
      <name>user</name>
      <uri>http://ubuntuusers.local:8080/user/user/</uri>
    </author>
    <id>http://ikhaya.ubuntuusers.local:8080/2023/12/09/article-subject/#comment_1</id>
    <summary type="html">&lt;p&gt;Text&lt;/p&gt;</summary>
  </entry>
</feed>
''')
