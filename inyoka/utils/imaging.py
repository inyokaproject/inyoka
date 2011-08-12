# -*- coding: utf-8 -*-
"""
    inyoka.utils.imaging
    ~~~~~~~~~~~~~~~~~~~~

    This module implements some helper methods to generate thumbnails

    :copyright: 2011 by the Project Name Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import os
from contextlib import closing
from hashlib import sha1

from django.conf import settings
from django.utils.encoding import force_unicode
from PIL import Image

from inyoka.utils.urls import is_external_target


def _get_box(img, width, height):
    if width and height:
        return (int(width), int(height))
    elif width and not height:
        return (int(width), int(img.size[1]))
    elif height and not width:
        return (int(img.size[0]), int(height))


def parse_dimensions(dimensions):
    if dimensions:
        if 'x' in dimensions:
            width, height = dimensions.split('x', 1)
        else:
            width = dimensions
            height = ''
        try:
            width = int(width)
        except ValueError:
            width = None
        try:
            height = int(height)
        except ValueError:
            height = None
    else:
        width = height = None

    return width, height


def fix_colorspace(image, grayscale=False, replace_alpha=False):
    """Convert an image to the correct color space.

    :param image: an PIL Image instance.
    :param grayscale:  grayscale the image object.
    :param replace_alpha: Replace the transparency layer with a solid color.
                          E.g ``replace_alpha='#fff'``.
    """
    if grayscale and image.mode != 'L':
        return image.convert('L')

    if image.mode in ('L', 'RGB'):
        return image

    has_alpha = (image.mode == 'P' and 'transparency' in image.info)

    if image.mode == 'RGBA' or has_alpha:
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        if not replace_alpha:
            return image
        base = Image.new('RGBA', image.size, replace_alpha)
        base.paste(image)
        image = base

    return image.convert('RGB')


def get_thumbnail(location, destination, width=None, height=None, force=False):
    """
    This function generates a thumbnail for an uploaded image.
    It uses the media root to cache those thumbnails.  A script should delete
    thumbnails once a month to get rid of unused thumbnails.  The wiki will
    recreate thumbnails automatically.

    The return value is `None` if it cannot generate a thumbnail or the path
    for the thumbnail.  Join it with the media root or media URL to get the
    internal filename.  This method generates a PNG thumbnail.
    """
    if not width and not height:
        raise ValueError('neither with nor height given')

    if is_external_target(location):
        return None

    format, quality = ('png', '100')
    # force unicode because of posixpath
    destination = force_unicode(destination)
    destination = u'%s.%s' % (destination.rsplit('.', 1)[0], format)
    fn = os.path.join(settings.MEDIA_ROOT, destination)
    if os.path.exists(fn):
        return destination

    # get the source stream. if the location is an url we load it using
    # the urllib2 and convert it into a StringIO so that we can fetch the
    # data multiple times. If we are operating on a wiki page we load the
    # most recent revision and get the attachment as stream.
    try:
        src = open(os.path.join(settings.MEDIA_ROOT, location), 'rb')
    except IOError:
        return

    try:
        with closing(src) as src:
            img = Image.open(src)
            img = fix_colorspace(img)
            box = _get_box(img, width, height)
            if img.size > box:
                img.thumbnail(box, Image.ANTIALIAS)
            real_filename = os.path.join(settings.MEDIA_ROOT, destination)
            try:
                os.makedirs(os.path.dirname(real_filename))
            except OSError:
                pass
            img.save(real_filename, quality=100)
    except IOError:
        # the image could not be identified
        return

    # Return none if there were errors in thumbnail rendering, that way we can
    # raise 404 exceptions instead of raising 500 exceptions for the user.
    return destination


def clean_thumbnail_cache():
    """
    This should be called by a cron about once a week.  It automatically
    deletes external thumbnails (so that they expire over a time) and not
    referenced internal attachments (for example old revisions).

    It returns the list of deleted files *and* directories.  Keep in mind
    that the return value is more or less useless except for statistics
    because in the meantime something could have recreated a directory or
    even a file.
    """
    from inyoka.wiki.models import Page
    attachments = {}
    for page in Page.objects.iterator():
        latest_rev = page.revisions.latest()
        if latest_rev.attachment:
            filename = latest_rev.attachment.file
            # the utf-8 encoding is fishy. as long as django leaves it
            # undefined what it does with the filenames it's the best
            # we can do.
            hash = sha1(filename.encode('utf-8')).hexdigest()
            attachments[hash] = filename

    # get a snapshot of the files and folders when we start executing. This
    # is important because someone could change the files while we operate
    # on them
    thumb_folder = os.path.join(settings.MEDIA_ROOT, 'wiki', 'thumbnails')
    snapshot_filenames = set()
    for dirpath, dirnames, filenames in os.walk(thumb_folder):
        dirpath = os.path.join(thumb_folder, dirpath)
        for filename in filenames:
            snapshot_filenames.add(os.path.join(dirpath, filename))

    to_delete = set()
    for filename in snapshot_filenames:
        basename = os.path.basename(filename)
        # something odd ended up there or the file was external.
        # delete it now.
        if len(basename) < 41 or basename[40] == 'e':
            to_delete.add(filename)
        else:
            hash = basename[:40]
            if hash not in attachments:
                to_delete.add(filename)

    # now delete all the collected files.
    probably_empty_dirs = set()
    deleted = []
    for filename in to_delete:
        try:
            os.remove(filename)
        except (OSError, IOError):
            continue
        probably_empty_dirs.add(os.path.dirname(filename))
        deleted.append(filename)

    # maybe we can get rid of some directories. try that
    for dirname in probably_empty_dirs:
        try:
            os.rmdir(dirname)
        except OSError:
            continue
        deleted.append(dirname)

    return deleted
