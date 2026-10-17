"""
tests.utils.test_files
~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2007-2026 by the Inyoka Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
import io
from unittest import TestCase

from inyoka.utils.files import sha256_io


class TestSha256Io(TestCase):

    def test_bytesio(self):
        sha256sum = sha256_io(io.BytesIO(b'foobarbaz'))
        self.assertEqual(sha256sum, "97df3588b5a3f24babc3851b372f0ba71a9dcdded43b14b9d06961bfc1707d9d")

    def test_bigfile(self):
        sha256sum = sha256_io(io.BytesIO(b'foobarbaz' * 5120))
        self.assertEqual(sha256sum, "f803d540ff555cdde48f6d9137dc8c403eaa5eda8ab70a26e746c3c6aa60336b")
