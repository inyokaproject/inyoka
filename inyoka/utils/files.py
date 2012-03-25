# -*- coding: utf-8 -*-
"""
    inyoka.utils.files
    ~~~~~~~~~~~~~~~~~~

    File related utilities.

    :copyright: (c) 2007-2012 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import itertools
import os.path

from django.core.files.storage import FileSystemStorage
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


def get_filename(filename, file=None):
    """
    Returns a save filename (CAUTION: strips path components!) and adds a
    proper extension.
    """
    mime = None
    if file is not None:
        file.seek(0)
        mime = magic.from_buffer(file.read(1024), mime=True)
        file.seek(0)

    filename = utils.secure_filename(filename) or 'Noname'
    if mime:
        return fix_extension(filename, mime)
    else:
        return filename


class MaxLengthStorageMixin(object):
    """
    Mixin for Django's storage system to ensure max_length is taken into
    account.
    """
    max_length = 100 # Default FileField length.

    def get_available_name(self, name):
        """
        Returns a filename that's free on the target storage system, and
        available for new content to be written to.
        """
        if '../' in name or '../' in os.path.normpath(name):
            raise ValueError('Invalid Path.')

        dir_name, file_name = os.path.split(name)
        file_root, file_ext = os.path.splitext(file_name)

        if len(name) > self.max_length:
            length = self.max_length - len(file_ext) - len(dir_name) - 1
            name = os.path.join(dir_name, file_root[:length] + file_ext)

        # If the filename already exists, add an underscore and a number (before
        # the file extension, if one exists) to the filename until the generated
        # filename doesn't exist.
        count = itertools.count(1)
        while self.exists(name):
            # file_ext includes the dot.
            c = count.next()
            length = self.max_length - len(file_ext) - len(str(c)) - 1 - len(dir_name) - 1
            name = os.path.join(dir_name, "%s_%s%s" % (file_root[:length], c, file_ext))

        return name


class InyokaFSStorage(MaxLengthStorageMixin, FileSystemStorage):
    """
    Default storage backend for Inyoka.
    """
