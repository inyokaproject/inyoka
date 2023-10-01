# -*- coding: utf-8 -*-
"""
    inyoka.utils.imaging
    ~~~~~~~~~~~~~~~~~~~~

    This module implements some helper methods to generate thumbnails

    :copyright: (c) 2011-2023 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import os
from contextlib import closing

from django.conf import settings
from django.utils.encoding import force_str
from PIL import Image

from inyoka.utils.urls import is_safe_domain


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
    It uses the media root to cache those thumbnails. A script should delete
    thumbnails once a month to get rid of unused thumbnails. The wiki will
    recreate thumbnails automatically.

    The return value is `None` if it cannot generate a thumbnail.
    Join it with the media root or media URL to get the
    internal filename. This method generates a PNG thumbnail.
    """
    if not width and not height:
        raise ValueError('neither width nor height given')

    if not is_safe_domain(location):
        return None

    format = 'png'
    # force unicode because of posixpath
    destination = force_str(destination)
    destination = '%s.%s' % (destination.rsplit('.', 1)[0], format)
    fn = os.path.join(settings.MEDIA_ROOT, destination)
    if os.path.exists(fn):
        return destination

    # get the source stream. If we are operating on a wiki page we load the
    # most recent revision and get the attachment as stream.
    try:
        with Image.open(os.path.join(settings.MEDIA_ROOT, location)) as img:
            img = fix_colorspace(img)
            box = _get_box(img, width, height)
            if img.size > box:
                img.thumbnail(box, Image.Resampling.LANCZOS)
            real_filename = os.path.join(settings.MEDIA_ROOT, destination)
            os.makedirs(os.path.dirname(real_filename), exist_ok=True)
            img.save(real_filename, quality=100)
    except IOError:
        # the image could not be identified
        return

    # Return none if there were errors in thumbnail rendering, that way we can
    # raise 404 exceptions instead of raising 500 exceptions for the user.
    return destination
