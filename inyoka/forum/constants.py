"""
    inyoka.forum.constants
    ~~~~~~~~~~~~~~~~~~~~~~

    Various constants for the forum application.

    :copyright: (c) 2011-2023 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from PIL import Image
from django.utils.translation import gettext_lazy

from inyoka.portal.utils import get_ubuntu_versions

# initialize PIL to make Image.ID available
Image.init()
SUPPORTED_IMAGE_TYPES = ['image/%s' % m.lower() for m in Image.ID]


POSTS_PER_PAGE = 15
TOPICS_PER_PAGE = 30
CACHE_PAGES_COUNT = 5

UBUNTU_DISTROS = {
    'none': gettext_lazy('No Ubuntu'),
    'edubuntu': gettext_lazy('Edubuntu'),
    'kubuntu': gettext_lazy('Kubuntu'),
    'server': gettext_lazy('Server'),
    'ubuntu': gettext_lazy('Ubuntu'),
    'xubuntu': gettext_lazy('Xubuntu'),
    'lubuntu': gettext_lazy('Lubuntu'),
    'gnome': gettext_lazy('Ubuntu GNOME'),
    'touch': gettext_lazy('Ubuntu Touch'),
    'mate': gettext_lazy('Ubuntu MATE'),
    'budgie': gettext_lazy('Ubuntu Budgie'),
    'unity': gettext_lazy('Ubuntu Unity'),
}

UBUNTU_DISTROS_SELECT_EXCLUDE = (
    'gnome',
)


def get_simple_version_choices():
    return [(v.number, str(v)) for v in get_ubuntu_versions() if v.is_active()]


def get_version_choices():
    return [('', gettext_lazy('Version'))] + get_simple_version_choices()


def get_distro_choices(exclude: bool=False):
    if exclude:
        UBUNTU_DISTROS_SELECT = UBUNTU_DISTROS.copy()

        for key in UBUNTU_DISTROS_SELECT_EXCLUDE:
            UBUNTU_DISTROS_SELECT.pop(key)

        return [('', gettext_lazy('Distribution'))] + list(UBUNTU_DISTROS_SELECT.items())

    return [('', gettext_lazy('Distribution'))] + list(UBUNTU_DISTROS.items())
