# -*- coding: utf-8 -*-
"""
    inyoka.utils.files
    ~~~~~~~~~~~~~~~~~~

    File related utilities.

    :copyright: (c) 2007-2020 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import itertools
import os.path

from django.core.files.storage import FileSystemStorage


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

    def get_available_name(self, name, max_length=None):
        """
        Returns a filename that's free on the target storage system, and
        available for new content to be written to.

        :raise: A ValueError if `name` contains ``../`` or ends with ``..``.
        :raise: An AssertionError is raised if the file root cannot be at least
            :py:attr:`min_file_root_length` characters long. Independent of
            the actual file root. This makes the handling of an incrementing
            counter at the end of the file root much simpler.
        """
        normalized = os.path.normpath(name)
        if '../' in name or '../' in normalized or name.endswith('..'):
            raise ValueError('Invalid Path.')

        dir_name, file_name = os.path.split(name)
        # file_ext incl. '.'
        file_root, file_ext = os.path.splitext(file_name)
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

        # If the filename already exists, add an underscore and a number
        # (before the file extension, if one exists) to the filename until
        # the generated filename doesn't exist.
        count = itertools.count(1)
        while self.exists(name):
            # file_ext includes the dot.
            c = count.next()
            cs = str(c)
            # +1 for '_'
            strip = (l_file_root + len(cs) + 1) - allowed_length
            if strip > 0:
                new_file_root = file_root[:-strip]
            else:
                new_file_root = file_root

            name = os.path.join(dir_name, "%s_%s%s" %
                                (new_file_root, cs, file_ext))

        return name


class InyokaFSStorage(MaxLengthStorageMixin, FileSystemStorage):
    """
    Default storage backend for Inyoka.
    """
    # TODO: Sice django 1.8 django supports max_length. So this class can be
    #       removed be finding all places in inyoka where storage.save() is
    #       used and set the max_length attribute
