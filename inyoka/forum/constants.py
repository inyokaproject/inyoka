#-*- coding: utf-8 -*-
"""
    inyoka.forum.constants
    ~~~~~~~~~~~~~~~~~~~~~~

    Various constants for the forum application.

    :copyright: (c) 2011-2012 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from PIL import Image
from django.utils.translation import ugettext_lazy
from inyoka.portal.utils import UBUNTU_VERSIONS


# initialize PIL to make Image.ID available
Image.init()
SUPPORTED_IMAGE_TYPES = ['image/%s' % m.lower() for m in Image.ID]


POSTS_PER_PAGE = 15
TOPICS_PER_PAGE = 30
CACHE_PAGES_COUNT = 5

UBUNTU_DISTROS_LEGACY = {
    'none': ugettext_lazy(u'Not specified'),
    'edubuntu': ugettext_lazy('Edubuntu'),
    'kubuntu': ugettext_lazy('Kubuntu'),
    'kubuntu-kde4': ugettext_lazy(u'Kubuntu (KDE 4)'),
    'server': ugettext_lazy('Server'),
    'ubuntu': ugettext_lazy('Ubuntu'),
    'xubuntu': ugettext_lazy('Xubuntu'),
    'lubuntu': ugettext_lazy('Lubuntu'),
    'unity': 'Unity',
}

UBUNTU_DISTROS = [
    ('none', ugettext_lazy(u'Not specified')),
    ('edubuntu', ugettext_lazy('Edubuntu')),
    ('kubuntu', ugettext_lazy('Kubuntu')),
    ('server', ugettext_lazy('Server')),
    ('ubuntu', ugettext_lazy('Ubuntu')),
    ('xubuntu', ugettext_lazy('Xubuntu')),
    ('lubuntu', ugettext_lazy('Lubuntu')),
    ('unity', ugettext_lazy('Unity')),
]

SIMPLE_VERSION_CHOICES = [
    (v.number, str(v)) for v in UBUNTU_VERSIONS
                       if v.is_active()]
VERSION_CHOICES = [('', ugettext_lazy('Version'))] + SIMPLE_VERSION_CHOICES
DISTRO_CHOICES = [('', ugettext_lazy('Distribution'))] + UBUNTU_DISTROS
