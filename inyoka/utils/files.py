# -*- coding: utf-8 -*-
"""
    inyoka.utils.files
    ~~~~~~~~~~~~~~~~~~

    File related utilities.

    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from mimetypes import guess_all_extensions, guess_extension
from werkzeug import utils

from inyoka.utils import magic


def fix_extension(filename, mime):
    """Adds a proper extension according to the mimetype"""
    possible_extensions = guess_all_extensions(mime)

    # we have no idea about this filetype at all.
    if not possible_extensions:
        return filename

    ext = '.' + filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    retval = None

    if ext in possible_extensions:
        retval = filename
    else:
        if mime == 'image/jpeg':
            ext = '.jpg'
        elif mime == 'application/xml' and ext in ('.svg', '.html'):
            pass
        elif mime == 'application/octet-stream' and ext == '.mo':
            pass
        else:
            ext = guess_extension(mime)
        retval = filename.rsplit('.', 1)[0] + ext

    return retval


def get_filename(filename, file):
    """
    Returns a save filename (CAUTION: strips path components!) and adds a
    proper extension
    """
    file.seek(0)
    mime = magic.from_buffer(file.read(1024), mime=True)
    file.seek(0)

    filename = utils.secure_filename(filename) or 'Noname'
    return fix_extension(filename, mime)
