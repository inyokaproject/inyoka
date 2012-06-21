#-*- coding: utf-8 -*-
import datetime
from django.test import TestCase
from inyoka.utils.localflavor.en.dates import naturalday_in_running_text
from inyoka.utils.test import override_settings


class TestDates(TestCase):
    @override_settings(LANGUAGE_CODE='en-en')
    def test_naturalday(self):
        self.assertNotIn('on', naturalday_in_running_text(datetime.date.today()))
        self.assertIn('on', naturalday_in_running_text(datetime.date.today() +
                                                      datetime.timedelta(days=2)))
