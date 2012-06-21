#-*- coding: utf-8 -*-

from django.test import TestCase
from django.http import HttpRequest
from inyoka.utils.decorators import try_localflavor
from inyoka.utils.local import local
from inyoka.utils.test import override_settings

@try_localflavor
def localflavor_testfunction():
    return "orginal"

@try_localflavor
def localflavor_testfunction2():
    return "orginal"


class TestDecorators(TestCase):
    @override_settings(LANGUAGE_CODE='en-en')
    def test_try_localflavor(self):
        local.request = HttpRequest()
        self.assertEqual("localized", localflavor_testfunction())
        self.assertEqual("orginal", localflavor_testfunction2())
