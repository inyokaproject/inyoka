"""
    inyoka.utils.files
    ~~~~~~~~~~~~~~~~~~

    File related utilities.

    :copyright: (c) 2007-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from werkzeug import utils


def get_filename(filename, file=None):
    """
    Returns a save filename (CAUTION: strips path components!).
    """
    return utils.secure_filename(filename) or 'Noname'
