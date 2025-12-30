"""
tests.utils.test_clamav
~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2025-2026 by the Inyoka Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

import base64
import io
from typing import IO, Final
from unittest import skip
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import override_settings

from inyoka.utils.clamav import (
    Clamav,
    ClamdConnectionError,
    scan_all_media_files,
    validate_file_infection,
)
from inyoka.utils.test import TestCase

EICAR_base64: Final[bytes] = (
    b'WDVPIVAlQEFQWzRcUFpYNTQoUF4pN0NDKTd9JEVJQ0FSLVNUQU5EQVJELUFOVElWSVJVUy1URVNULUZJTEUhJEgrSCoK'
)
EICAR: Final[IO[bytes]] = io.BytesIO(base64.b64decode(EICAR_base64))


class TestClamAV(TestCase):
    def test_simple_text(self) -> None:
        test_bytes = io.BytesIO(b'Testcontent without a file')
        validate_file_infection(test_bytes)

    def test_buffer_too_long(self) -> None:
        test_bytes = io.BytesIO(b'Test' * 26 * 1024 * 1024)  # 104 MB

        with self.assertRaisesMessage(
            ValidationError,
            'The attachment could not be checked against malware and thus is not allowed to be uploaded. Please contact the website administrator.',
        ):
            validate_file_infection(test_bytes)

    def test_eicar(self) -> None:
        with self.assertRaisesMessage(ValidationError, 'File is infected with malware'):
            validate_file_infection(EICAR)

    def test_invalid_port(self) -> None:
        s = Clamav(host='127.0.0.1', port=1337)
        with self.assertRaisesMessage(ClamdConnectionError, 'Connection refused'):
            s.__enter__()

    def test_invalid_address(self) -> None:
        s = Clamav(host='notexisting.test')
        with self.assertRaisesMessage(
            ClamdConnectionError, 'Name or service not known'
        ):
            s.__enter__()

    @override_settings(CLAMAV_HOST='notexisting.test')
    def test_invalid_address2(self) -> None:
        test_bytes = io.BytesIO(b'Testcontent without a file')
        with self.assertRaisesMessage(
            ValidationError,
            'The attachment could not be checked against malware and thus is not allowed to be uploaded. Please contact the website administrator.',
        ):
            validate_file_infection(test_bytes)

        with self.assertLogs('inyoka', level='INFO') as cm:
            scan_all_media_files()

            self.assertEqual(
                cm.output,
                [
                    'ERROR:inyoka:Clamav seems to be unavailable [Errno -2] Name or service not known'
                ],
            )

    @override_settings(MEDIA_ROOT='/tmp/not-existing-path')
    def test_scan_all_media_files(self) -> None:
        with self.assertLogs('inyoka', level='INFO') as cm:
            scan_all_media_files()

            self.assertEqual(
                cm.output,
                [
                    "ERROR:inyoka:clamav result: Clamav.ClamavResult(filename='/tmp/not-existing-path', reason='File path check failure: No such file or directory.', status='ERROR')",
                    "ERROR:inyoka:clamav result: Clamav.ClamavResult(filename='/tmp/not-existing-path', reason='File path check failure: No such file or directory.', status='ERROR')",
                ],
            )

    @patch('inyoka.utils.clamav.Clamav.ClamavResult')
    @override_settings(MEDIA_ROOT='/tmp/not-existing-path')
    def test_scan_all_media_files__malware(self, c) -> None:
        c.contains_malware = lambda x: True

        with self.assertLogs('inyoka', level='INFO'):
            scan_all_media_files()

    def test_parse_response_OK(self) -> None:
        msg = 'stream: OK'
        parsed = Clamav._parse_response(msg)

        self.assertEqual(parsed.filename, 'stream')
        self.assertEqual(parsed.reason, None)
        self.assertEqual(parsed.status, 'OK')

    def test_parse_response_ERROR(self) -> None:
        msg = '/home/media: File path check failure: No such file or directory. ERROR'
        parsed = Clamav._parse_response(msg)

        self.assertEqual(parsed.filename, '/home/media')
        self.assertEqual(
            parsed.reason, 'File path check failure: No such file or directory.'
        )
        self.assertEqual(parsed.status, 'ERROR')

    def test_parse_response_FOUND(self) -> None:
        msg = 'stream: Eicar-Test-Signature FOUND'
        parsed = Clamav._parse_response(msg)

        self.assertEqual(parsed.filename, 'stream')
        self.assertEqual(parsed.reason, 'Eicar-Test-Signature')
        self.assertEqual(parsed.status, 'FOUND')

    @override_settings(CLAMAV_ENABLE=False)
    def test_clamav_disabled(self) -> None:
        test_bytes = io.BytesIO(b'Testcontent without a file')
        with self.assertLogs('inyoka', level='INFO') as cm:
            validate_file_infection(test_bytes)

            self.assertEqual(cm.output, ['INFO:inyoka:Clamav disabled'])

        with self.assertLogs('inyoka', level='INFO') as cm:
            scan_all_media_files()

            self.assertEqual(cm.output, ['INFO:inyoka:Clamav disabled'])

    @skip
    def test_reject_file_uploads_starting_with_a_dot(self) -> None:
        self.assertTrue(False)
