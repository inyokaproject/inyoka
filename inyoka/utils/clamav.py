"""
inyoka.utils.clamav
~~~~~~~~~~~~~~~~~~~

Provides utilities to scan file uploads with clamav.

Inspired by
<https://github.com/chander/django-clamav> (git repo commit 0e412cca2c70f74e317abe8d2ed542e8dc786f42)
and
<https://github.com/graingert/python-clamd/blob/master/src/clamd/__init__.py>
(git repo commit 24b21e8c875b88ba8a03c29ba2ef04887a8d56c5).
Both are licensed under the LGPL.

:copyright: (c) 2025-2026 by the Inyoka Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

import re
import socket
import struct
import sys
from dataclasses import dataclass, field
from typing import IO, AnyStr, Generator

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from inyoka.utils.logger import logger

if sys.version_info < (3, 11):
    from typing import TypeVar

    Self = TypeVar('Self', bound='Clamav')
else:
    from typing import Self


class ClamdError(Exception):
    """Base class for all clamd related errors."""
    pass


class ClamdBufferTooLongError(ClamdError):
    """Class to indicate that a too big file was provided to clamd via INSTREAM."""


class ClamdConnectionError(ClamdError):
    """Class for communication errors with clamd."""


class ClamdMalwareFound(ClamdError):
    """Class to indicate that malware was found."""


@dataclass
class Clamav:
    """
    Allows to use clamav via a network TCP socket.
    This class should be used with a context manager like::

            with Clamav() as scanner:
                result = scanner._do_something_()

    See the clamd(8) man page for details about the clamav commands.
    (F.e. https://man.archlinux.org/man/clamd.8)
    """

    @dataclass
    class ClamavResult:
        """Small helper class that represents the clamav result for one file."""

        filename: str
        reason: str | None
        status: str

        def contains_malware(self) -> bool:
            return self.status == 'FOUND'

        def is_error(self) -> bool:
            return self.status == 'ERROR'

    host: str = field(default_factory=lambda: settings.CLAMAV_HOST)
    port: int = field(default_factory=lambda: settings.CLAMAV_PORT)
    timeout: float | None = None  # socket timeout
    max_chunk_size: int = field(default_factory=lambda: settings.CLAMAV_MAX_CHUNK_SIZE)

    def __enter__(self) -> Self:
        try:
            self.clamd_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.clamd_socket.connect((self.host, self.port))
            self.clamd_socket.settimeout(self.timeout)

            return self
        except socket.error as e:
            self.__exit__(*sys.exc_info())
            raise ClamdConnectionError(e)

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.clamd_socket.close()

    def multiscan(self, file: str) -> Generator[ClamavResult, None, None]:
        """
        Scan a file or directory given by its *absolute path*.
        Normally, uses multiple threads and won't stop on error or finding.
        """

        self._send_command('MULTISCAN', file)

        for result in self._recv_response():
            logger.debug(result)
            yield self._parse_response(result)

    def instream(self, buffer: IO[AnyStr]) -> ClamavResult:
        """
        Scans the passed buffer for malware.
        Raises an exception, if malware was found or an error occurred.
        """

        buffer.seek(0)  # ensure to start at beginning of file

        self._send_command('INSTREAM')

        while chunk := buffer.read(self.max_chunk_size):
            size = struct.pack(b'!L', len(chunk))
            try:
                self.clamd_socket.send(size + chunk)
            except BrokenPipeError as e:
                self.__exit__(*sys.exc_info())
                raise ClamdConnectionError(e)
        self.clamd_socket.send(struct.pack(b'!L', 0))

        result_string = next(self._recv_response())
        logger.debug(result_string)

        buffer.seek(0)

        if 'INSTREAM size limit exceeded. ERROR' in result_string:
            raise ClamdBufferTooLongError(result_string)

        result = self._parse_response(result_string)
        if result.contains_malware():
            raise ClamdMalwareFound(result)

        return result

    def _send_command(self, cmd: str, *args) -> None:
        """
        Prefix all commands with `n`, as we will use `\n` terminated strings
        (*not* null-terminated ones). See `man clamd` for details.
        """
        concat_args = ''
        if args:
            concat_args = ' ' + ' '.join(args)

        cmd = f'n{cmd}{concat_args}\n'.encode('utf-8')
        self.clamd_socket.send(cmd)

    def _recv_response(self) -> Generator[str, None, None]:
        """
        Receive a response from clamd.
        All whitespace characters are stripped from each line.
        """
        try:
            with self.clamd_socket.makefile('rb') as f:
                for line in f:
                    stripped_line = line.decode('utf-8').strip()
                    if stripped_line:
                        yield stripped_line
        except (socket.error, socket.timeout) as e:
            self.__exit__(*sys.exc_info())
            raise ClamdConnectionError(f'Error while reading from socket: {e.args}')

    @staticmethod
    def _parse_response(msg: str) -> ClamavResult:
        """
        Parses responses for commands.
        """
        scan_response = re.compile(
            r'^(?P<path>.*?): ((?P<virus>.+) )?(?P<status>(FOUND|OK|ERROR))$'
        )

        filename, reason, status = scan_response.match(msg).group(
            'path', 'virus', 'status'
        )

        return Clamav.ClamavResult(filename, reason, status)


def validate_file_infection(file: IO[AnyStr]) -> None:
    """
    Validator function that can be used in a django form field.

    Simple example usage:
    - inside a form
      ``upload_file = forms.FileField(validators=[validate_file_infection])``
    - inside a model
      ``document = models.FileField(validators=[validate_file_infection])``
    """

    if not settings.CLAMAV_ENABLE:
        logger.info('Clamav disabled')
        return

    try:
        with Clamav() as scanner:
            result = scanner.instream(file)
    except ClamdMalwareFound:
        raise ValidationError(_('File is infected with malware'), code='infected')
    except ClamdError as e:
        logger.error(f'Clamav seems to be unavailable {e}')
        raise ValidationError(
            _(
                'The attachment could not be checked against malware and thus is not allowed to be uploaded. Please contact the website administrator.'
            ),
            code='clamav-unavailable',
        )

    logger.info(f'clamav result: {result}')


def scan_all_media_files() -> None:
    """
    Scans all media files for malware.
    Findings and errors will be added to the python log.
    """

    if not settings.CLAMAV_ENABLE:
        logger.info('Clamav disabled')
        return

    try:
        with Clamav() as scanner:
            result = list(scanner.multiscan(settings.MEDIA_ROOT))
    except ClamdError as e:
        logger.error(f'Clamav seems to be unavailable {e}')
        return

    for r in result:
        msg = f'clamav result: {r}'
        if r.contains_malware():
            logger.warning(msg)
        elif r.is_error():
            logger.error(msg)
        else:
            logger.info(msg)
