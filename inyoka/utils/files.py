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
    #: Default FileField length.
    max_length = 100

    #: The minimum length for a filename. This should assure a unique
    #: filename, even if it needs to be enumerated.
    min_file_root_length = 8

    def get_available_name(self, name):
        """
        Returns a filename that's free on the target storage system, and
        available for new content to be written to.

        :raise: A ValueError if `name` contains ``../`` or ends with ``..``.
        :raise: An AssertionError is raised if the file root cannot be at least
            :py:attr:`min_file_root_length` characters long. Independent of
            the actual file root. This makes the handling of an incrementing
            counter at the end of the file root much simpler.
        """
        if '../' in name or '../' in os.path.normpath(name) \
            or name.endswith('..'):
            raise ValueError('Invalid Path.')

        dir_name, file_name = os.path.split(name)
        file_root, file_ext = os.path.splitext(file_name) # file_ext incl '.'
        l_dir_name = len(dir_name)
        l_file_root = len(file_root)
        l_file_ext = len(file_ext)

        allowed_length = self.max_length - l_dir_name - l_file_ext
        if l_dir_name > 0:
            # We need to take care of '/' between dir_name and file_name
            allowed_length -= 1

        if allowed_length < self.min_file_root_length:
            raise AssertionError(u'Available file name length too short!')

        if len(name) > self.max_length:
            file_root = file_root[:allowed_length]
            l_file_root = allowed_length
            name = os.path.join(dir_name, "%s%s" % (file_root, file_ext))

        # If the filename already exists, add an underscore and a number (before
        # the file extension, if one exists) to the filename until the generated
        # filename doesn't exist.
        count = itertools.count(1)
        while self.exists(name):
            # file_ext includes the dot.
            c = count.next()
            cs = str(c)
            strip = (l_file_root + len(cs) + 1) - allowed_length # +1 for '_'
            if strip > 0:
                new_file_root = file_root[:-strip]
            else:
                new_file_root = file_root

            name = os.path.join(dir_name, "%s_%s%s" % (new_file_root, cs, file_ext))

        return name


class InyokaFSStorage(MaxLengthStorageMixin, FileSystemStorage):
    """
    Default storage backend for Inyoka.
    """
