"""
    tests.apps.utils.test_middleware
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test Inyoka-custom middlewares.

    :copyright: (c) 2012-2025 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.conf import settings
from django.test import RequestFactory

from inyoka.middlewares.common import CommonServicesMiddleware
from inyoka.utils.test import InyokaClient, TestCase


class TestNULByte(TestCase):

    client_class = InyokaClient

    def test_get_null(self):
        url = f'http://{ settings.BASE_DOMAIN_NAME }/1%00%EF/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_get_null_calender(self):
        url = f'http://{ settings.BASE_DOMAIN_NAME }/2023/11/18/lpd-2023-10\x00EF2522/ics/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)


class TestServiceMiddleware(TestCase):

    def test_invalid_module(self):
        url = f'http://{ settings.BASE_DOMAIN_NAME }/?__service__=%40%40rKhiI&component=&hide='
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_http_not_found(self):
        url = f'http://{ settings.BASE_DOMAIN_NAME }/?__service__=portal.toggle_sidebar%27%7C%7CDBMS_PIPE.RECEIVE'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_control_characters_stripped_in_post(self):
        self.factory = RequestFactory()
        data = {'foobar': 'control characters \x08 \x0f in text'}
        request = self.factory.post('/', data)
        CommonServicesMiddleware(lambda x: x).process_request(request)
        self.assertEqual(request.POST['foobar'], 'control characters   in text')
