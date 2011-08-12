# -*- coding: utf-8 -*-
"""
    inyoka.utils
    ~~~~~~~~~~~~

    Various application independent utilities.

    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from urllib import urlencode
from urllib2 import urlopen, HTTPError
from hashlib import md5
from simplejson import load


BASE_URL = 'http://www.gravatar.com/avatar/'
SECURE_BASE_URL = 'https://secure.gravatar.com/avatar/'
PROFILE_URL = 'http://www.gravatar.com/'
RATINGS = ('g', 'pg', 'r', 'x')
MAX_SIZE = 512
MIN_SIZE = 1
DEFAULTS = ('404', 'mm', 'identicon', 'monsterid', 'wavatar', 'retro')


def email_hash(string):
    return md5(string.strip().lower()).hexdigest()


def get_gravatar(email, secure=False, rating='g', size=80, default='mm'):
    """Generate a link to the users' Gravatar.

    >>> get_gravatar('gridaphobe@gmail.com')
    'http://www.gravatar.com/avatar/16b87da510d278999c892cdbdd55c1b6?s=80&r=g&d=mm'
    """
    assert rating.lower() in RATINGS
    assert MIN_SIZE <= size <= MAX_SIZE

    url = SECURE_BASE_URL if secure else BASE_URL

    options = {'s': size, 'r': rating, 'd': default}
    url += email_hash(email) + '?' + urlencode(options)
    return url


def get_profile(email):
    """Retrieves the profile data of the user.

    :return: A dictionary representing the profile.
    """
    profile = None
    try:
        url = u'%s%s.json' % (PROFILE_URL, email_hash(email))
        profile = load(urlopen(url))['entry'][0]
    except (HTTPError, IndexError):
        pass
    return profile
