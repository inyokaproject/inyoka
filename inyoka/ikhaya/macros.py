# -*- coding: utf-8 -*-
"""
    inyoka.ikhaya.macros
    ~~~~~~~~~~~~~~~~~~~~

    Macros for Ikhaya.

    :copyright: (c) 2012-2023 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import os

from django.conf import settings
from django.dispatch import receiver

from inyoka.markup import nodes
from inyoka.portal.models import StaticFile
from inyoka.utils.urls import url_for
from inyoka.utils.imaging import get_thumbnail
from inyoka.wiki.signals import build_picture_node


@receiver(build_picture_node)
def build_ikhaya_picture_node(sender, context, format, **kwargs):
    if not context.application == 'ikhaya':
        return

    target, width, height = (sender.target, sender.width, sender.height)
    try:
        file = StaticFile.objects.get(identifier=target)
        if (width or height) and os.path.exists(file.file.path):
            tt = target.rsplit('.', 1)
            dimension = '%sx%s' % (width and int(width) or '',
                                   height and int(height) or '')
            target = '%s%s.%s' % (tt[0], dimension, tt[1])

            destination = os.path.join(settings.MEDIA_ROOT, 'portal/thumbnails', target)
            thumb = get_thumbnail(file.file.path, destination, width, height)
            if thumb:
                source = os.path.join(settings.MEDIA_URL, 'portal/thumbnails', thumb.rsplit('/', 1)[1])
            else:
                # fallback to the orginal file
                source = os.path.join(settings.MEDIA_URL, file.file.name)
        else:
            source = url_for(file)
        img = nodes.Image(source, sender.alt, class_='image-' +
                          (sender.align or 'default'), title=sender.title)
        if (width or height) and file is not None:
            return nodes.Link(url_for(file), [img])
        return img
    except StaticFile.DoesNotExist:
        return
