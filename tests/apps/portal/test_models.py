# -*- coding: utf-8 -*-
"""
    tests.apps.portal.test_models
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test portal models.

    :copyright: (c) 2012-2019 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from inyoka.portal.models import Linkmap


class TestLinkmapModel(TestCase):

    error_message_token = u'Only lowercase letters, - and _ allowed. Numbers as postfix.'

    def token(self, token):
        Linkmap(token=token, url='http://example.test').full_clean()

    def test_valid_token(self):
        self.token('debian_de')
        self.token('kubuntu-de')
        self.token('canonicalsubdomain')
        self.token('sourceforge2')

    def test_invalid_token__umlaut(self):
        with self.assertRaisesMessage(ValidationError, self.error_message_token):
            self.token(u'öäüß')

        with self.assertRaisesMessage(ValidationError, self.error_message_token):
            self.token(u'jkoijoijö')

    def test_invalid_token__uppercase(self):
        with self.assertRaisesMessage(ValidationError, self.error_message_token):
            self.token('Adfv')

        with self.assertRaisesMessage(ValidationError, self.error_message_token):
            self.token('dfvD')

    def url(self, url):
        Linkmap(token='example', url=url).full_clean()

    def test_valid_url(self):
        self.url('http://example.test')
        self.url('https://startpage.test/do/search?cat=web&language=deutsch&query=PAGE&ff=')
        self.url('https://PAGE.wordpress.test/')
        self.url('https://web.archive.test/web/*/https://')

    def test_invalid_url(self):
        with self.assertRaisesMessage(ValidationError, u'Enter a valid URL.'):
            self.url('foo.test')

        with self.assertRaisesMessage(ValidationError, u'Enter a valid URL.'):
            self.url('apt:')

        with self.assertRaisesMessage(ValidationError, u'Enter a valid URL.'):
            self.url('apt://')

        with self.assertRaisesMessage(ValidationError, u'Enter a valid URL.'):
            self.url('https://PAGE')

    def test_uniqueness_token(self):
        token = 'example'
        Linkmap.objects.create(token=token, url='http://example.test')

        with self.assertRaises(IntegrityError):
            Linkmap.objects.create(token=token, url='http://example2.test')
