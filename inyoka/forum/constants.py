#-*- coding: utf-8 -*-
"""
    inyoka.forum.constants
    ~~~~~~~~~~~~~~~~~~~~~~

    Various constants for the forum application.

    :copyright: (c) 2011-2015 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from PIL import Image
from django.utils.translation import ugettext_lazy

from inyoka.portal.utils import get_ubuntu_versions

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


def get_simple_version_choices():
    return [(v.number, str(v)) for v in get_ubuntu_versions() if v.is_active()]


def get_version_choices():
    return [('', ugettext_lazy('Version'))] + get_simple_version_choices()


def get_distro_choices():
    return [('', ugettext_lazy('Distribution'))] + UBUNTU_DISTROS
