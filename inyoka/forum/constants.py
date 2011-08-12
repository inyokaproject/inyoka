#-*- coding: utf-8 -*-
"""
    inyoka.forum.constants
    ~~~~~~~~~~~~~~~~~~~~~~

    Various constants for the forum application.

    :copyright: (c) 2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from PIL import Image
from inyoka.utils.urls import href


# initialize PIL to make Image.ID available
Image.init()
SUPPORTED_IMAGE_TYPES = ['image/%s' % m.lower() for m in Image.ID]


POSTS_PER_PAGE = 15
TOPICS_PER_PAGE = 30
CACHE_PAGES_COUNT = 5


class UbuntuVersion(object):
    """holds the ubuntu versions. implement this as a model in SA!"""
    def __init__(self, number, codename, lts=False, active=False, class_=None,
                 current=False):
        self.number = number
        self.codename = codename
        self.lts = lts
        self.active = active or current
        self.class_ = class_
        self.current = current
        self.link = href('wiki', codename)

    def __str__(self):
        return u'%s (%s)' % (self.number, self.codename)


UBUNTU_VERSIONS = [
    UbuntuVersion('keine', 'Keine Angabe', active=True),
    UbuntuVersion('4.10', 'Warty Warthog'),
    UbuntuVersion('5.04', 'Hoary Hedgehog'),
    UbuntuVersion('5.10', 'Breezy Badger'),
    UbuntuVersion('6.06', 'Dapper Drake', lts=True),
    UbuntuVersion('6.10', 'Edgy Eft'),
    UbuntuVersion('7.04', 'Feisty Fawn'),
    UbuntuVersion('7.10', 'Gutsy Gibbon'),
    UbuntuVersion('8.04', 'Hardy Heron', lts=True, active=True),
    UbuntuVersion('8.10', 'Intrepid Ibex'),
    UbuntuVersion('9.04', 'Jaunty Jackalope'),
    UbuntuVersion('9.10', 'Karmic Koala'),
    UbuntuVersion('10.04', 'Lucid Lynx', lts=True, active=True),
    UbuntuVersion('10.10', 'Maverick Meerkat', active=True),
    UbuntuVersion('11.04', 'Natty Narwhal', current=True),
    UbuntuVersion('11.10', 'Oneiric Ocelot', class_='unstable', current=True),
]

UBUNTU_DISTROS_LEGACY = {
    'keine': 'Keine Angabe',
    'edubuntu': 'Edubuntu',
    'kubuntu': 'Kubuntu',
    'kubuntu-kde4': u'Kubuntu (KDE 4)',
    'server': 'Server',
    'ubuntu': 'Ubuntu',
    'xubuntu': 'Xubuntu',
    'unity': 'Unity',
}

UBUNTU_DISTROS = [
    ('keine', 'Keine Angabe'),
    ('edubuntu', 'Edubuntu'),
    ('kubuntu', 'Kubuntu'),
    ('server', 'Server'),
    ('ubuntu', 'Ubuntu'),
    ('xubuntu', 'Xubuntu'),
    ('unity', 'Unity'),
]


VERSION_CHOICES = [('', 'Version')] + \
                  [(v.number, str(v)) for v in filter(lambda v: v.active, UBUNTU_VERSIONS)]
DISTRO_CHOICES = [('', 'Distribution')] + UBUNTU_DISTROS
