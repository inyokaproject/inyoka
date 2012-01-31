#-*- coding: utf-8 -*-
"""
    inyoka.forum.constants
    ~~~~~~~~~~~~~~~~~~~~~~

    Various constants for the forum application.

    :copyright: (c) 2011-2012 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from PIL import Image
from inyoka.portal.utils import UBUNTU_VERSIONS
from inyoka.utils.urls import href


# initialize PIL to make Image.ID available
Image.init()
SUPPORTED_IMAGE_TYPES = ['image/%s' % m.lower() for m in Image.ID]


POSTS_PER_PAGE = 15
TOPICS_PER_PAGE = 30
CACHE_PAGES_COUNT = 5

#: TODO fix translation
UBUNTU_DISTROS_LEGACY = {
    'keine': 'Keine Angabe',
    'edubuntu': 'Edubuntu',
    'kubuntu': 'Kubuntu',
    'kubuntu-kde4': u'Kubuntu (KDE 4)',
    'server': 'Server',
    'ubuntu': 'Ubuntu',
    'xubuntu': 'Xubuntu',
    'lubuntu': 'Lubuntu',
    'unity': 'Unity',
}

#: TODO fix translation
UBUNTU_DISTROS = [
    ('keine', 'Keine Angabe'),
    ('edubuntu', 'Edubuntu'),
    ('kubuntu', 'Kubuntu'),
    ('server', 'Server'),
    ('ubuntu', 'Ubuntu'),
    ('xubuntu', 'Xubuntu'),
    ('lubuntu', 'Lubuntu'),
    ('unity', 'Unity'),
]

SIMPLE_VERSION_CHOICES = [(v.number, str(v)) for v in UBUNTU_VERSIONS \
        if v.is_active()]
#: TODO fix translation
VERSION_CHOICES = [('', 'Version')] + SIMPLE_VERSION_CHOICES
DISTRO_CHOICES = [('', 'Distribution')] + UBUNTU_DISTROS
