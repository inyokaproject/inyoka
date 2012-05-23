#-*- coding: utf-8 -*-
import datetime
from django.test import TestCase
from inyoka.utils.dates import naturalday_with_adverb


class TestDates(TestCase):

    def test_naturalday(self):
        self.assertNotIn('on', naturalday_with_adverb(datetime.date.today()))
        self.assertIn('on', naturalday_with_adverb(datetime.date.today() +
                                                      datetime.timedelta(days=2)))
