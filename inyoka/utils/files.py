"""
    inyoka.utils.files
    ~~~~~~~~~~~~~~~~~~

    File related utilities.

    :copyright: (c) 2007-2026 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import hashlib
from typing import BinaryIO

from werkzeug import utils


def get_filename(filename, file=None):
    """
    Returns a save filename (CAUTION: strips path components!).
    """
    return utils.secure_filename(filename) or 'Noname'


def sha256_io(file: BinaryIO) -> str:
    sha256_hash = hashlib.sha256()

    file.seek(0)

    for block in iter(lambda: file.read(2048), b""):
        sha256_hash.update(block)

    file.seek(0)

    return sha256_hash.hexdigest()
