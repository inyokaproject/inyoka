.. _utils-files:

==============
File Utilities
==============

.. py:module:: inyoka.utils.files

.. py:currentmodule:: inyoka.utils.files


.. py:function:: fix_extension(filename, mime)

    Adds a proper extension according to the mimetype


.. py:function:: get_filename(filename[, file=None])

    Returns a save filename (CAUTION: strips path components!) and adds a
    proper extension.


.. py:class:: MaxLengthStorageMixin(object)

    Mixin for Django's storage system to ensure max_length is taken into
    account.

    .. py:attribute:: max_length

        Maximum FileField length. Defaults to ``100``.

    .. py:attribute:: min_file_root_length

        The minimum length for a filename that must be available. This should
        assure a unique filename, even if it needs to be enumerated. Defaults
        to ``8``.

    .. py:method:: get_available_name(name)

        Returns a filename that's free on the target storage system, and
        available for new content to be written to. The return value is not
        longer than :py:attr:`max_length`

        :raise: A ValueError if `name` contains ``../`` or ends with ``..``.

        :raise: An AssertionError is raised if the file root cannot be at least
            :py:attr:`min_file_root_length` characters long. Independent of the
            actual file root. This makes the handling of an incrementing
            counter at the end of the file root much simpler.


.. py:class:: InyokaFSStorage(MaxLengthStorageMixin, FileSystemStorage)

    Default storage backend for Inyoka. This combines the default Django
    :py:class:`~django.core.files.storage.FileSystemStorage`
