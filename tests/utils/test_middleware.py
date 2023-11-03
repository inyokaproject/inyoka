"""
    tests.apps.utils.test_middleware
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test Inyoka-custom middlewares.

    :copyright: (c) 2012-2023 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.conf import settings

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
